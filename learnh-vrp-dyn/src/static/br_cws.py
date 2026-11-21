"""BR-CWS: Clarke & Wright con aleatorización sesgada dentro de un multiarranque.

Secciones 4.1 y 5.2 del paper, sin caja negra ni caja blanca. Dos bucles:

1. `build_vrp_sol` (Algorithm 1): construye UNA solución. Es el mismo bucle que
   `g_cws.build_vrp_sol`, salvo la línea 5: en vez de coger siempre la mejor
   arista, saca un número aleatorio por cada arista y elige su posición con una
   distribución geométrica de parámetro p,
       P(posición = k) ∝ p (1 − p)^k,
   así que las aristas con más ahorro siguen siendo las más probables.
   p → 1 recupera el voraz; p → 0 es una elección uniforme. El paper usa
   p ∈ (0,1; 0,3).
2. `multi_start`: repite esa construcción `n_iter` veces. El generador `rng` se
   comparte y avanza en cada llamada, así que cada iteración recibe números
   aleatorios distintos y construye una solución distinta. Se devuelve la mejor.
   La solución voraz es el punto de partida, así que nunca sale peor que CWS.
"""

import random

from ..cws import (
    compute_savings,
    generate_base_solution,
    merge_feasible,
    merge_routes,
)
from ..utils.biased_random import geometric_index
from ..utils.cvrplib import Instance
from ..vrp_objects import Solution, create_nodes_and_edges
from . import g_cws


def build_vrp_sol(inst: Instance, p: float, rng: random.Random) -> Solution:
    """Algorithm 1 con elección sesgada, sin caja negra ni caja blanca."""
    nodes, edges = create_nodes_and_edges(inst)
    savings = compute_savings(edges)  # parejas (i, j) en orden decreciente de ahorro
    solution = generate_base_solution(nodes)
    while len(savings):
        index = geometric_index(len(savings), p, rng)  # número aleatorio → posición
        edge = edges[savings.get(index)]  # coger la arista
        savings.delete(index)  # y quitarla de la lista
        if merge_feasible(edge, inst.capacity):
            merge_routes(edge, solution)
    return solution


def multi_start(inst: Instance, p: float, n_iter: int, seed: int) -> Solution:
    """Mejor solución entre la voraz y `n_iter` construcciones BR-CWS."""
    rng = random.Random(seed)
    best = g_cws.build_vrp_sol(inst)
    for _ in range(n_iter):
        sol = build_vrp_sol(inst, p, rng)
        if sol.cost < best.cost:
            best = sol
    return best
