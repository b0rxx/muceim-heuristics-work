"""D-BR-CWS: BR-CWS dinámico, la learnheuristic del paper (Algorithms 1 y 2 completos).

Igual que static/br_cws.py, salvo que los costes ya no son distancias fijas:

- La caja negra revela el coste real de cada ruta cuando se construye
  (Algorithm 1, líneas 11-12) y la caja blanca aprende de él (línea 13).
- Los ahorros se calculan con costes reales y predichos (Algorithm 2):
      ahorro(i, j) = coste real(ruta de i) + coste real(ruta de j) − predicción WB(ruta unida)
  y se recalculan tras cada unión (Algorithm 1, línea 14), porque las rutas y la
  caja blanca han cambiado.

Algorithm 2 recorre las parejas i < j como el paper y predice una sola ruta
unida por pareja, … i | j …, que es como la deja después mergeRoutes. Con costes
que dependen de la carga, el sentido contrario … j | i … costaría distinto; el
paper no lo considera y aquí tampoco.

Algorithm 2 se escribe línea a línea como en el paper, pero sin los dos bucles:
cada variable (i_route, j_route, merged_route, costes, ahorros) es un array con
una posición por pareja (i, j), y numpy hace todas las parejas a la vez.
"""

import random
from dataclasses import dataclass, fields
from operator import attrgetter

import numpy as np

from .. import cws
from ..cws import Savings, edge_loads, merge_feasible
from ..utils.biased_random import geometric_index
from ..utils.cvrplib import Instance
from ..vrp_objects import Node, Route, Solution, create_nodes_and_edges
from .black_box import BlackBox
from .white_box import WhiteBox


def route_features(route: Route) -> tuple[float, float]:
    """(Σ c_e, Σ c_e Q_e) de la ruta en su sentido: lo que usa la caja blanca."""
    dist = w = 0.0
    for edge, load in edge_loads(route):
        dist += edge.cost
        w += edge.cost * load
    return dist, w


@dataclass
class Routes:
    """Las rutas (`Route`) de varios nodos exteriores x a la vez, por columnas, vistas desde x."""

    node: np.ndarray  # id de x
    x: np.ndarray  # coordenadas de x
    y: np.ndarray
    depot_cost: np.ndarray  # c_x0 = c_0x
    demand: np.ndarray  # carga de la ruta
    cost: np.ndarray  # coste real de la ruta (caja negra)
    dist: np.ndarray  # Σ c_e de la ruta
    w_first: np.ndarray  # Σ c_e Q_e recorriendo la ruta con x al principio
    w_last: np.ndarray  # Σ c_e Q_e recorriendo la ruta con x al final

    @classmethod
    def of(cls, nodes: list[Node]) -> "Routes":
        """getRoute de cada nodo: su `node.in_route`."""
        routes: list[Route] = [node.in_route for node in nodes]  # type: ignore[misc]
        demand = np.array([route.demand for route in routes], dtype=float)
        dist, w = np.array([route_features(route) for route in routes]).T
        # al revés, cada arco lleva la carga que en este sentido ya se ha dejado: Q'_e = carga − Q_e
        w_rev = demand * dist - w
        starts = np.array([route.edges[0].end is node for node, route in zip(nodes, routes)])  # x al principio
        return cls(
            node=np.array([node.id for node in nodes]),
            x=np.array([node.x for node in nodes]),
            y=np.array([node.y for node in nodes]),
            depot_cost=np.array([node.nd_edge.cost for node in nodes]),  # type: ignore[union-attr]
            demand=demand,
            cost=np.array([route.cost for route in routes]),
            dist=dist,
            w_first=np.where(starts, w, w_rev),
            w_last=np.where(starts, w_rev, w),
        )

    def get_route(self, k: np.ndarray) -> "Routes":
        """Las rutas de las posiciones k."""
        return Routes(*(getattr(self, field.name)[k] for field in fields(self)))


def get_exterior_nodes(solution: Solution) -> list[Node]:
    """Nodos exteriores (extremos de ruta) de la solución, en orden de id."""
    ends = {node for route in solution.routes for node in (route.edges[0].end, route.edges[-1].origin)}
    return sorted(ends, key=attrgetter("id"))


def merge_routes(i_route: Routes, j_route: Routes) -> tuple[np.ndarray, np.ndarray]:
    """mergeRoutes sin construir la ruta: (Σ c_e, Σ c_e Q_e) de cada ruta unida A … i | j … B.

    Respecto a A y B por separado, desaparecen i → 0 (vacío) y 0 → j y aparece
    i → j. Los arcos de A que quedan y el arco i → j llevan además la carga de B.
    """
    c_ij = np.hypot(i_route.x - j_route.x, i_route.y - j_route.y)
    a_dist = i_route.dist - i_route.depot_cost  # A sin i → 0
    b_dist = j_route.dist - j_route.depot_cost  # B sin 0 → j
    dist = a_dist + c_ij + b_dist
    w = i_route.w_last + j_route.w_first + j_route.demand * (a_dist + c_ij - j_route.depot_cost)
    return dist, w


def generate_base_solution(nodes: list[Node], black_box: BlackBox) -> Solution:
    """generateBaseSolution: solución dummy 0 → i → 0, con el coste real de cada ruta.

    Algorithm 2 (líneas 9-10, getCost ▷ Black Box) parte del coste real de las
    rutas, así que la caja negra lo revela al crearlas.
    """
    solution = cws.generate_base_solution(nodes)
    for route in solution.routes:
        solution.update(route, black_box.get_real_cost(route))
    return solution


def compute_savings(solution: Solution, white_box: WhiteBox) -> Savings:
    """Algorithm 2 (COMPUTESAVINGS). Cada variable tiene una posición por pareja (i, j)."""
    exterior_nodes = get_exterior_nodes(solution)  # línea 3
    i, j = np.triu_indices(len(exterior_nodes), k=1)  # líneas 4-5: todas las parejas i < j
    routes = Routes.of(exterior_nodes)  # la ruta de cada nodo exterior
    i_route = routes.get_route(i)  # línea 6
    j_route = routes.get_route(j)  # línea 7
    merged_route = merge_routes(i_route, j_route)  # línea 8
    i_real_cost = i_route.cost  # línea 9
    j_real_cost = j_route.cost  # línea 10
    merged_predicted_cost = white_box.predict_cost(*merged_route)  # línea 11
    route_savings = i_real_cost + j_real_cost - merged_predicted_cost  # línea 12
    keep = route_savings > 0  # línea 13: add routeSavings to savings (solo positivos, como en CWS)
    order = np.argsort(-route_savings[keep], kind="stable")  # línea 16: savings.sort, orden decreciente
    i, j, saving = i_route.node[keep][order], j_route.node[keep][order], route_savings[keep][order]
    return Savings(list(zip(i.tolist(), j.tolist(), saving.tolist())))


def build_vrp_sol(
    inst: Instance, p: float, rng: random.Random, black_box: BlackBox, white_box: WhiteBox
) -> Solution:
    """Algorithm 1 (BUILDDVRPSOL): BR-CWS con caja negra y caja blanca."""
    nodes, edges = create_nodes_and_edges(inst)  # edges[i, j]: Edge i → j, i < j
    solution = generate_base_solution(nodes, black_box)  # línea 2
    savings = compute_savings(solution, white_box)  # línea 3
    while len(savings):  # línea 4
        index = geometric_index(len(savings), p, rng)  # línea 5
        edge = edges[savings.get(index)]  # línea 6
        savings.delete(index)  # línea 7
        if merge_feasible(edge, inst.capacity):  # línea 8
            route = cws.merge_routes(edge, solution)  # líneas 9-10
            real_cost = black_box.get_real_cost(route)  # línea 11
            solution.update(route, real_cost)  # línea 12
            white_box.update(*route_features(route), real_cost)  # línea 13
            savings = compute_savings(solution, white_box)  # línea 14
    return solution


def multi_start(
    inst: Instance, p: float, n_iter: int, seed: int, black_box: BlackBox, white_box: WhiteBox
) -> Solution:
    """Mejor solución (por coste real) de `n_iter` construcciones.

    La caja blanca se comparte entre construcciones: sigue aprendiendo de una a otra.
    """
    rng = random.Random(seed)
    best = build_vrp_sol(inst, p, rng, black_box, white_box)
    for _ in range(n_iter - 1):
        sol = build_vrp_sol(inst, p, rng, black_box, white_box)
        if sol.cost < best.cost:
            best = sol
    return best


def forecast_cost(solution: Solution, white_box: WhiteBox) -> float:
    """Coste de la solución según la caja blanca (DFC en la Tabla 1)."""
    dist, w = np.array([route_features(route) for route in solution.routes]).T
    return float(white_box.predict_cost(dist, w).sum())
