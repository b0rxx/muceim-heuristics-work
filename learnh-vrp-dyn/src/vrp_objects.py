"""Clases Node, Edge, Route y Solution del CWS de las transparencias (vrp_objects.py, A. A. Juan).

Mismos atributos que en las transparencias, con nombres en snake_case:
inRoute → in_route, isInterior → is_interior, dnEdge → dn_edge, ndEdge → nd_edge,
invEdge → inv_edge.
"""

from __future__ import annotations

import math

from .utils.cvrplib import Instance


class Node:
    def __init__(self, id: int, x: float, y: float, demand: int):
        self.id = id  # identificador del nodo (depósito = 0)
        self.x = x  # coordenada x euclídea
        self.y = y  # coordenada y euclídea
        self.demand = demand  # demanda (0 en el depósito, positiva en los clientes)
        self.in_route: Route | None = None  # ruta a la que pertenece el nodo
        self.is_interior = False  # un nodo interior no está conectado al depósito
        self.dn_edge: Edge | None = None  # arco depósito → nodo
        self.nd_edge: Edge | None = None  # arco nodo → depósito


class Edge:
    def __init__(self, origin: Node, end: Node):
        self.origin = origin  # nodo origen del arco
        self.end = end  # nodo destino del arco
        self.cost = 0.0  # coste del arco
        self.savings = 0.0  # ahorro del arco (Clarke & Wright)
        self.inv_edge: Edge | None = None  # arco inverso


class Route:
    def __init__(self):
        self.cost = 0.0  # coste de la ruta
        self.edges: list[Edge] = []  # arcos de la ruta, en orden
        self.demand = 0  # demanda total que cubre la ruta

    @property
    def nodes(self) -> list[int]:
        """Clientes en orden de visita, sin el depósito: lo que usan la caja negra y las figuras."""
        return [edge.end.id for edge in self.edges[:-1]]

    def reverse(self) -> None:
        """P. ej. 0 → 2 → 6 → 0 pasa a 0 → 6 → 2 → 0."""
        self.edges = [edge.inv_edge for edge in reversed(self.edges)]  # type: ignore[misc]


class Solution:
    def __init__(self):
        self.routes: list[Route] = []  # rutas de la solución
        self.cost = 0.0  # coste de la solución
        self.demand = 0  # demanda total que cubre la solución

    def update(self, route: Route, real_cost: float) -> None:
        """Algorithm 1, línea 12 del paper: la ruta pasa a costar lo que ha revelado la caja negra."""
        self.cost += real_cost - route.cost
        route.cost = real_cost


def create_nodes_and_edges(inst: Instance) -> tuple[list[Node], dict[tuple[int, int], Edge]]:
    """Nodos y arcos de la instancia, como en las transparencias (cws_heuristic.py).

    - Un `Node` por fila (0 = depósito) y, en cada cliente, sus arcos depósito → nodo
      (`dn_edge`) y nodo → depósito (`nd_edge`).
    - Un `Edge` i → j por cada pareja de clientes i < j, con su inverso, su coste y
      su ahorro de Clarke & Wright s_ij = c_0i + c_0j − c_ij.

    Costes euclídeos sin redondear y simétricos. Devuelve los nodos y los arcos i < j, por pareja: edges[i, j].
    """
    nodes = [Node(i, float(x), float(y), int(d)) for i, ((x, y), d) in enumerate(zip(inst.coords, inst.demand))]
    depot = nodes[0]
    for node in nodes[1:]:
        dn_edge, nd_edge = Edge(depot, node), Edge(node, depot)
        dn_edge.inv_edge, nd_edge.inv_edge = nd_edge, dn_edge
        dn_edge.cost = nd_edge.cost = math.dist((node.x, node.y), (depot.x, depot.y))
        node.dn_edge, node.nd_edge = dn_edge, nd_edge

    edges = {}
    for i, i_node in enumerate(nodes[1:-1], start=1):
        for j_node in nodes[i + 1 :]:
            ij_edge, ji_edge = Edge(i_node, j_node), Edge(j_node, i_node)
            ij_edge.inv_edge, ji_edge.inv_edge = ji_edge, ij_edge
            ij_edge.cost = ji_edge.cost = math.dist((i_node.x, i_node.y), (j_node.x, j_node.y))
            ij_edge.savings = ji_edge.savings = i_node.nd_edge.cost + j_node.dn_edge.cost - ij_edge.cost  # type: ignore[union-attr]
            edges[i_node.id, j_node.id] = ij_edge
    return nodes, edges
