"""Instancias CVRPLIB del paper (Arnau, Juan y Serra 2018, Tabla 1): lectura.

Cada instancia está en data/ con dos ficheros:

    <nombre>.vrp   instancia (formato TSPLIB)
    <nombre>.sol   mejor solución conocida (BKS): rutas + "Cost <valor>"

Distancias: euclídeas sin redondear, como en el paper (sus costes de la Tabla 1
no son enteros). Las BKS de CVRPLIB usan la euclídea redondeada (TSPLIB EUC_2D).
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Las 30 instancias de la Tabla 1 del paper.
INSTANCES = (
    "A-n32-k5", "A-n38-k5", "A-n55-k9", "A-n60-k9", "A-n61-k9", "A-n65-k9", "A-n80-k10",
    "B-n35-k5", "B-n50-k7", "B-n52-k7", "B-n64-k9", "B-n67-k10", "B-n78-k10",
    "E-n101-k14", "E-n22-k4", "E-n23-k3", "E-n30-k3", "E-n33-k4", "E-n51-k5",
    "E-n76-k10", "E-n76-k14",
    "F-n135-k7",
    "M-n101-k10", "M-n200-k16",
    "P-n22-k8", "P-n40-k5", "P-n50-k10", "P-n55-k15", "P-n65-k10", "P-n70-k10",
)


@dataclass(frozen=True)
class Instance:
    name: str
    capacity: int
    coords: np.ndarray  # (n+1, 2); fila 0 = depósito
    demand: np.ndarray  # (n+1,);   demand[0] = 0
    dist: np.ndarray  # (n+1, n+1) simétrica, euclídea sin redondear

    @property
    def n_customers(self) -> int:
        return len(self.demand) - 1


def read_instance(path: Path) -> Instance:
    header: dict[str, str] = {}
    sections: dict[str, list[list[str]]] = {}
    current = None
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line == "EOF":
            continue
        if line.endswith("_SECTION"):
            current = sections.setdefault(line, [])
        elif current is None:
            key, value = line.split(":", 1)
            header[key.strip()] = value.strip()
        else:
            current.append(line.split())

    if header["EDGE_WEIGHT_TYPE"] != "EUC_2D":
        raise ValueError(f"{path.name}: solo se soporta EUC_2D, no {header['EDGE_WEIGHT_TYPE']}")
    depots = [int(row[0]) for row in sections["DEPOT_SECTION"] if row[0] != "-1"]
    if depots != [1]:
        raise ValueError(f"{path.name}: se espera un único depósito en el nodo 1, hay {depots}")

    coords = np.array([[float(x), float(y)] for _, x, y in sections["NODE_COORD_SECTION"]])
    demand = np.array([int(d) for _, d in sections["DEMAND_SECTION"]])
    euclid = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(axis=-1))
    return Instance(
        name=header["NAME"],
        capacity=int(header["CAPACITY"]),
        coords=coords,
        demand=demand,
        dist=euclid,
    )


def read_bks(path: Path) -> tuple[list[list[int]], float]:
    """Rutas (clientes numerados 1..n, sin depósito) y coste de la mejor solución conocida."""
    routes: list[list[int]] = []
    cost = None
    for line in path.read_text().splitlines():
        if line.startswith("Route"):
            routes.append([int(v) for v in line.split(":", 1)[1].split()])
        elif line.startswith("Cost"):
            cost = float(line.split()[1])
    if cost is None:
        raise ValueError(f"{path.name}: falta la línea Cost")
    return routes, cost
