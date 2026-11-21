"""Caja negra (BB, ecuación 2 del paper): emula el sistema real.

El método de resolución no la conoce: solo le pide el coste real de una ruta
una vez construida (Algorithm 1, línea 11). Cada llamada es una realización
nueva, con su propio error ϵ en cada arco.
"""

import numpy as np

from ..cws import edge_loads
from ..utils.cvrplib import Instance
from ..vrp_objects import Route

EPS = 1e-3  # ϵ ~ U[−10⁻³, 10⁻³]


class BlackBox:
    """c*_ij = c_ij (1 + Q_i^k / C − 1/2 + ϵ) = c_ij (1/2 + Q_i^k / C + ϵ).

    Q_i^k es la carga del vehículo al salir del nodo i en la ruta k y C la
    capacidad: β1 = 1/C y β2 = −1/2 en la ecuación (1). Un arco cuesta entre
    1/2 (vehículo vacío) y 3/2 (lleno) veces su coste medio c_ij.
    """

    def __init__(self, inst: Instance, seed: int):
        self.inst = inst
        self.rng = np.random.default_rng(seed)

    def get_real_cost(self, route: Route) -> float:
        e = self.rng.uniform(-EPS, EPS, len(route.edges))
        c = self.inst.capacity
        return float(sum(edge.cost * (0.5 + load / c + ei) for (edge, load), ei in zip(edge_loads(route), e)))
