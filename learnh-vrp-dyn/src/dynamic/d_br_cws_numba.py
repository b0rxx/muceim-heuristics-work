"""D-BR-CWS con numba: mismo algoritmo y mismos resultados que d_br_cws.py, más rápido.

Lo que más tarda en d_br_cws.py es Algorithm 2 (compute_savings, ~70 % del tiempo): numpy
crea una docena de arrays temporales por pareja y `LinearRegression.predict` de
scikit-learn valida la entrada en cada llamada. Aquí:

- `_savings`: un solo bucle compilado sobre las parejas i < j que hace merge_routes,
  predice los dos sentidos y ordena los ahorros, sin arrays intermedios.
- La caja blanca predice con sus coeficientes (`white_box.beta`) en vez de con
  `predict`: sin término independiente, predict = b0 · Σ c_e + b1 · Σ c_e Q_e / C.
- `_two_opt`: el 2-opt de d_br_cws.py sobre una matriz de costes, evaluando cada inversión
  sin construir la ruta candidata.

Caja negra, caja blanca (aprendizaje), Routes.of y mergeRoutes siguen en Python.
main.py ejecuta las dos versiones y compara sus tiempos.
"""

import math
import random

import numpy as np
from numba import njit

from .. import cws
from ..cws import Savings, merge_feasible
from ..utils.biased_random import geometric_index
from ..utils.cvrplib import Instance
from ..vrp_objects import Node, Route, Solution, create_nodes_and_edges
from .black_box import BlackBox
from .d_br_cws import Edges, Routes, generate_base_solution, get_edge, get_exterior_nodes, route_features
from .white_box import WhiteBox


@njit(cache=True)
def _savings(node, x, y, depot_cost, demand, cost, dist, w_first, w_last, b0, b1, capacity):
    """Algorithm 2 de d_br_cws.py para todas las parejas i < j: (origen, destino, ahorro) en orden decreciente."""
    m = len(node)
    n_pairs = m * (m - 1) // 2
    origin = np.empty(n_pairs, np.int64)
    end = np.empty(n_pairs, np.int64)
    saving = np.empty(n_pairs)
    k = 0
    for i in range(m):
        a_dist = dist[i] - depot_cost[i]  # A sin i → 0
        for j in range(i + 1, m):
            c_ij = math.hypot(x[i] - x[j], y[i] - y[j])
            b_dist = dist[j] - depot_cost[j]  # B sin 0 → j
            d = a_dist + c_ij + b_dist
            w = w_last[i] + w_first[j] + demand[j] * (a_dist + c_ij - depot_cost[j])
            w_rev = (demand[i] + demand[j]) * d - w
            ij_cost = b0 * d + b1 * (w / capacity)
            ji_cost = b0 * d + b1 * (w_rev / capacity)
            forward = ij_cost <= ji_cost
            s = cost[i] + cost[j] - (ij_cost if forward else ji_cost)
            if s > 0:
                origin[k] = node[i] if forward else node[j]
                end[k] = node[j] if forward else node[i]
                saving[k] = s
                k += 1
    order = np.argsort(-saving[:k], kind="mergesort")  # estable, como d_br_cws.py
    return origin[:k][order], end[:k][order], saving[:k][order]


def compute_savings(solution: Solution, white_box: WhiteBox) -> Savings:
    """Algorithm 2 de d_br_cws.py en `_savings`."""
    r = Routes.of(get_exterior_nodes(solution))
    b0, b1 = white_box.beta
    origin, end, saving = _savings(
        r.node, r.x, r.y, r.depot_cost, r.demand, r.cost, r.dist, r.w_first, r.w_last, b0, b1, white_box.capacity
    )
    return Savings(list(zip(origin.tolist(), end.tolist(), saving.tolist())))


@njit(cache=True)
def _features(seq, a, b, cost, demand, load):
    """(Σ c_e, Σ c_e Q_e) de seq con el tramo seq[a..b] invertido."""
    dist = w = 0.0
    prev = seq[0]
    for k in range(1, len(seq)):
        v = seq[a + b - k] if a <= k <= b else seq[k]
        c = cost[prev, v]
        dist += c
        w += c * load
        load -= demand[v]
        prev = v
    return dist, w


@njit(cache=True)
def _two_opt(seq, cost, demand, load, b0, b1, capacity):
    """2-opt de d_br_cws.py con mejor mejora según b0 · Σ c_e + b1 · Σ c_e Q_e / C. Devuelve (seq, ha mejorado)."""
    n = len(seq) - 2
    d, w = _features(seq, 0, 0, cost, demand, load)
    current = b0 * d + b1 * (w / capacity)
    improved = False
    while True:
        best, best_a, best_b = np.inf, 0, 0
        for a in range(1, n):
            for b in range(a + 1, n + 1):
                d, w = _features(seq, a, b, cost, demand, load)
                p = b0 * d + b1 * (w / capacity)
                if p < best:  # el primero de los mínimos, como np.argmin
                    best, best_a, best_b = p, a, b
        if best >= current - 1e-9:
            break
        seq = seq.copy()
        seq[best_a : best_b + 1] = seq[best_a : best_b + 1][::-1]
        current, improved = best, True
    return seq, improved


def two_opt(route: Route, nodes: list[Node], edges: Edges, cost: np.ndarray, white_box: WhiteBox) -> bool:
    """two_opt de d_br_cws.py con `_two_opt`. Cambia `route.edges` y devuelve si ha mejorado."""
    if len(route.edges) < 3:
        return False
    seq = np.array([route.edges[0].origin.id, *(edge.end.id for edge in route.edges)])
    b0, b1 = white_box.beta
    demand = np.array([node.demand for node in nodes], dtype=float)
    seq, improved = _two_opt(seq, cost, demand, float(route.demand), b0, b1, white_box.capacity)
    if improved:
        path = [nodes[k] for k in seq]
        route.edges = [get_edge(u, v, edges) for u, v in zip(path, path[1:])]
        for node in path[1:-1]:
            node.is_interior = node is not path[1] and node is not path[-2]
    return improved


def local_search(
    solution: Solution, nodes: list[Node], edges: Edges, cost: np.ndarray, black_box: BlackBox, white_box: WhiteBox
) -> None:
    """local_search de d_br_cws.py."""
    for route in solution.routes:
        if two_opt(route, nodes, edges, cost, white_box):
            real_cost = black_box.get_real_cost(route)
            solution.update(route, real_cost)
            white_box.update(*route_features(route), real_cost)


def build_vrp_sol(
    inst: Instance,
    p: float,
    rng: random.Random,
    black_box: BlackBox,
    white_box: WhiteBox,
    nodes: list[Node],
    edges: Edges,
    cost: np.ndarray,
) -> Solution:
    """build_vrp_sol de d_br_cws.py sobre nodos y arcos ya creados."""
    solution = generate_base_solution(nodes, black_box)
    savings = compute_savings(solution, white_box)
    while len(savings):
        index = geometric_index(len(savings), p, rng)
        i, j = savings.get(index)
        edge = get_edge(nodes[i], nodes[j], edges)
        savings.delete(index)
        if merge_feasible(edge, inst.capacity):
            route = cws.merge_routes(edge, solution)
            real_cost = black_box.get_real_cost(route)
            solution.update(route, real_cost)
            white_box.update(*route_features(route), real_cost)
            savings = compute_savings(solution, white_box)
    local_search(solution, nodes, edges, cost, black_box, white_box)
    return solution


def multi_start(
    inst: Instance, p: float, n_iter: int, seed: int, black_box: BlackBox, white_box: WhiteBox
) -> Solution:
    """multi_start de d_br_cws.py.

    Nodos y arcos se crean una vez y no en cada construcción (d_br_cws.py pierde ahí ~20 % del
    tiempo): los arcos no cambian y generate_base_solution reinicia in_route e is_interior.
    """
    nodes, edges = create_nodes_and_edges(inst)
    # math.dist como en create_nodes_and_edges: mismos costes de arco bit a bit
    cost = np.array([[math.dist(a, b) for b in inst.coords] for a in inst.coords])
    rng = random.Random(seed)
    best = build_vrp_sol(inst, p, rng, black_box, white_box, nodes, edges, cost)
    for _ in range(n_iter - 1):
        sol = build_vrp_sol(inst, p, rng, black_box, white_box, nodes, edges, cost)
        if sol.cost < best.cost:
            best = sol
    return best
