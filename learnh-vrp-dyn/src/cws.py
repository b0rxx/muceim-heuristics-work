"""Piezas comunes de Clarke & Wright Savings (CWS) para el CVRP.

Construcción de las transparencias (cws_heuristic.py, A. A. Juan) con las clases
de src/vrp_objects.py (nodos y arcos: `create_nodes_and_edges`), con los nombres del paper:

    compute_savings         ↔ Algorithm 2  COMPUTESAVINGS  (lista de ahorros)
    generate_base_solution  ↔ generateBaseSolution        (solución dummy)
    merge_feasible          ↔ mergeFeasible               (checkMergingConditions)
    merge_routes            ↔ mergeRoutes                 (unión iterativa)

Esta es la versión clásica (estática): sin caja negra ni caja blanca. Por eso
la lista de ahorros se calcula una sola vez y el coste de una ruta es su
distancia. Lo que en el paper son las líneas 11-14 del Algorithm 1 aquí se
reduce a actualizar el coste de la solución con el de la ruta unida.

El bucle del Algorithm 1 (BUILDDVRPSOL) está en cada variante, como `build_vrp_sol`:

    static/g_cws.py      voraz: siempre la mejor arista
    static/br_cws.py     aleatorización sesgada (geométrica) y multiarranque
    dynamic/d_br_cws.py  BR-CWS con caja negra y caja blanca (la learnheuristic)
"""

from collections.abc import Iterator
from dataclasses import dataclass
from operator import attrgetter

import numpy as np

from .utils.cvrplib import Instance
from .vrp_objects import Edge, Node, Route, Solution


def route_cost(nodes: list[int], dist: np.ndarray) -> float:
    path = [0, *nodes, 0]
    return float(dist[path[:-1], path[1:]].sum())


def edge_loads(route: Route) -> Iterator[tuple[Edge, int]]:
    """Cada arco de la ruta, en su sentido, con la carga Q_e con la que se recorre.

    Único sitio donde se define Q_e (caja negra y caja blanca). Es reparto: el
    vehículo sale del depósito con toda la carga de la ruta, deja la demanda de
    cada cliente que visita y vuelve vacío.
    """
    load = route.demand
    for edge in route.edges:
        yield edge, load
        load -= edge.end.demand


@dataclass
class Savings:
    """Lista de ahorros ordenada de mayor a menor: una fila (i, j, ahorro) por pareja."""

    rows: list[tuple[int, int, float]]

    def __len__(self) -> int:
        return len(self.rows)

    def get(self, index: int) -> tuple[int, int]:
        i, j, _ = self.rows[index]
        return i, j

    def delete(self, index: int) -> None:
        del self.rows[index]


def compute_savings(edges: dict[tuple[int, int], Edge]) -> Savings:
    """Lista de ahorros: los arcos i < j en orden decreciente de s_ij = c_0i + c_0j − c_ij.

    Al principio cada cliente es su propia ruta y es nodo exterior, así que el
    ahorro de unir las rutas de i y j es lo que se deja de recorrer: i → 0 y 0 → j.
    """
    ordered = sorted(edges.values(), key=attrgetter("savings"), reverse=True)  # estable: entre empates, (i, j) más bajos
    return Savings([(edge.origin.id, edge.end.id, edge.savings) for edge in ordered])


def generate_base_solution(nodes: list[Node]) -> Solution:
    """Solución dummy: un vehículo por cliente, 0 → i → 0. Reinicia el estado de los nodos."""
    sol = Solution()
    for node in nodes[1:]:
        route = Route()
        for edge in (node.dn_edge, node.nd_edge):
            route.edges.append(edge)  # type: ignore[arg-type]
            route.cost += edge.cost  # type: ignore[union-attr]
        route.demand = node.demand
        node.in_route = route
        node.is_interior = False  # conectado al depósito
        sol.routes.append(route)
        sol.cost += route.cost
        sol.demand += route.demand
    return sol


def merge_feasible(edge: Edge, capacity: int) -> bool:
    """checkMergingConditions: rutas distintas, i y j exteriores y la demanda conjunta cabe en un vehículo."""
    i_node, j_node = edge.origin, edge.end
    i_route, j_route = i_node.in_route, j_node.in_route
    return (
        i_route is not j_route
        and not i_node.is_interior
        and not j_node.is_interior
        and i_route.demand + j_route.demand <= capacity  # type: ignore[union-attr]
    )


def merge_routes(edge: Edge, solution: Solution) -> Route:
    """Une la ruta de j al final de la de i, quedando 0 … i | j … 0, y actualiza la solución."""
    i_node, j_node = edge.origin, edge.end
    i_route, j_route = i_node.in_route, j_node.in_route
    assert i_route is not None and j_route is not None
    # orientar las rutas como 0 … i → 0 y 0 → j … 0 y quitar esos dos arcos al depósito
    if i_route.edges[-1].origin is not i_node:
        i_route.reverse()
    if j_route.edges[0].end is not j_node:
        j_route.reverse()
    i_edge, j_edge = i_route.edges.pop(), j_route.edges.pop(0)
    # i y j dejan de estar unidos al depósito salvo si iban solos en su ruta
    i_node.is_interior = len(i_route.edges) > 1
    j_node.is_interior = len(j_route.edges) > 1
    i_route.edges += [edge, *j_route.edges]
    # j_route.cost y no Σ arcos: en la versión dinámica es el coste real
    i_route.cost += edge.cost + j_route.cost - i_edge.cost - j_edge.cost
    i_route.demand += j_route.demand
    for j_route_edge in j_route.edges:
        j_route_edge.origin.in_route = i_route  # j y el resto de clientes de su ruta
    solution.cost -= edge.savings
    solution.routes.remove(j_route)
    return i_route


def check(solution: Solution, inst: Instance, distances: bool = True) -> None:
    """Rutas encadenadas 0 → … → 0, cada cliente una vez, ninguna ruta sobre capacidad y costes coherentes.

    distances=False para soluciones dinámicas: el coste de cada ruta es una
    realización de la caja negra y no se puede recalcular.
    """
    for route in solution.routes:
        ids = [route.edges[0].origin.id] + [edge.end.id for edge in route.edges]
        assert ids[0] == ids[-1] == 0, f"la ruta no empieza y acaba en el depósito: {ids}"
        assert all(a.end is b.origin for a, b in zip(route.edges, route.edges[1:])), f"arcos no encadenados: {ids}"
    visited = sorted(node for route in solution.routes for node in route.nodes)
    assert visited == list(range(1, inst.n_customers + 1)), "clientes repetidos o sin servir"
    for route in solution.routes:
        assert route.demand == inst.demand[route.nodes].sum() <= inst.capacity, f"carga incorrecta: {route.nodes}"
        if distances:
            assert abs(route.cost - route_cost(route.nodes, inst.dist)) < 1e-6, f"coste incorrecto: {route.nodes}"
    assert abs(solution.cost - sum(route.cost for route in solution.routes)) < 1e-6
