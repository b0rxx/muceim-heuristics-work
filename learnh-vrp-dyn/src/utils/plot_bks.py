"""Comparación dinámica frente a la BKS: coste real del estático y de nuestra learnheuristic contra el de las rutas de la BKS.

Las rutas de la BKS (data/*.sol) pasan por la misma caja negra que nuestras
soluciones, cada una en su sentido más barato. Así todo se mide con la misma
vara; la BKS es una buena solución de referencia, no el óptimo del problema dinámico.

    python -m src.utils.plot_bks   # → figures/plots/bks_gap.png y tabla Markdown por pantalla
"""

import csv
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

from ..dynamic.black_box import BlackBox
from ..dynamic.d_br_cws import get_edge
from ..vrp_objects import Route, create_nodes_and_edges
from .cvrplib import read_bks, read_instance

ROOT = Path(__file__).parents[2]


def bks_real_cost(name: str) -> float:
    """Coste real de la BKS: cada ruta por la caja negra en el sentido más barato."""
    inst = read_instance(ROOT / "data" / f"{name}.vrp")
    nodes, edges = create_nodes_and_edges(inst)
    black_box = BlackBox(inst, 0)
    total = 0.0
    for customers in read_bks(ROOT / "data" / f"{name}.sol")[0]:
        seq = [nodes[0], *(nodes[i] for i in customers), nodes[0]]
        route = Route()
        route.edges = [get_edge(u, v, edges) for u, v in zip(seq, seq[1:])]
        route.demand = sum(node.demand for node in seq)  # carga de salida: edge_loads parte de aquí
        forward = black_box.get_real_cost(route)
        route.reverse()
        total += min(forward, black_box.get_real_cost(route))
    return total


SERIES = {"Estático (SRC)": "src", "D-BR-CWS (DRC)": "drc"}


def bks_gaps() -> tuple[list[str], np.ndarray, dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Instancias, coste real de la BKS, y coste y gap (%) de cada columna de SERIES."""
    rows = list(csv.DictReader(open(ROOT / "results" / "learnheuristic.csv")))
    names = [r["instance"] for r in rows]
    bks = np.array([bks_real_cost(name) for name in names])
    costs = {column: np.array([float(r[column]) for r in rows]) for column in SERIES.values()}
    gaps = {column: 100 * (cost - bks) / bks for column, cost in costs.items()}
    return names, bks, costs, gaps


if __name__ == "__main__":
    names, bks, costs, gaps = bks_gaps()
    f = lambda v: f"{v:.2f}".replace(".", ",")  # noqa: E731
    print("| Instancia | BKS (coste real) | SRC | DRC | gap SRC (%) | gap DRC (%) |")
    print("|---|---:|---:|---:|---:|---:|")
    for k, name in enumerate(names):
        print(f"| {name} | {f(bks[k])} | " + " | ".join(f(costs[c][k]) for c in costs) + " | " + " | ".join(f(gaps[c][k]) for c in gaps) + " |")
    print("| **Media** | | | | " + " | ".join(f"**{f(g.mean())}**" for g in gaps.values()) + " |")

    fig = Figure(figsize=(16, 6))
    ax = fig.subplots()
    x = np.arange(len(names))
    width = 0.4
    for k, (label, column) in enumerate(SERIES.items()):
        ax.bar(x + (k - 0.5) * width, gaps[column], width, label=f"{label} · media {gaps[column].mean():.2f} %")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x, names, rotation=60, ha="right", fontsize=8)
    ax.set_ylabel("gap frente al coste real de la BKS (%)")
    ax.set_title("Coste real frente al coste real de las rutas de la BKS (misma caja negra, mejor sentido)", fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    (ROOT / "figures" / "plots").mkdir(parents=True, exist_ok=True)
    fig.savefig(ROOT / "figures" / "plots" / "bks_gap.png", dpi=120)
