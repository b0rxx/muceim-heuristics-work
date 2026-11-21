"""G-CWS: Clarke & Wright voraz (greedy), el clásico.

En la línea 5 del Algorithm 1 coge siempre la arista de mayor ahorro (índice 0).
Las piezas comunes (nodos, ahorros, solución dummy, unión de rutas) están en src/cws.py.

    python -m src.static.g_cws A-n80-k10    # imprime la solución como en las transparencias
"""

import sys
from pathlib import Path

from ..cws import (
    compute_savings,
    generate_base_solution,
    merge_feasible,
    merge_routes,
)
from ..utils import cvrplib
from ..utils.cvrplib import Instance
from ..vrp_objects import Solution, create_nodes_and_edges


def build_vrp_sol(inst: Instance) -> Solution:
    """Algorithm 1 voraz, sin caja negra ni caja blanca."""
    nodes, edges = create_nodes_and_edges(inst)
    savings = compute_savings(edges)  # parejas (i, j) en orden decreciente de ahorro
    solution = generate_base_solution(nodes)
    while len(savings):
        edge = edges[savings.get(0)]  # voraz: siempre la mejor arista que queda
        savings.delete(0)
        if merge_feasible(edge, inst.capacity):
            merge_routes(edge, solution)
    return solution


if __name__ == "__main__":
    inst = cvrplib.read_instance(Path(__file__).resolve().parents[2] / "data" / f"{sys.argv[1]}.vrp")
    sol = build_vrp_sol(inst)
    print(f"Instance: {inst.name}, Vehicle Capacity {inst.capacity}")
    print(f"Cost of C&W savings sol = {sol.cost:.2f}")
    for route in sol.routes:
        print(f"Route: {'-'.join(map(str, [0, *route.nodes, 0]))} || cost = {route.cost:.2f}")
