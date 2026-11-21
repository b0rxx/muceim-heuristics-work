"""Salidas del experimento: CSV de resultados y figura de rutas."""

import csv
from pathlib import Path

from matplotlib.figure import Figure  # sin pyplot: no abre ventanas ni necesita backend

from .cvrplib import Instance
from ..vrp_objects import Solution


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def plot_solution(inst: Instance, sol: Solution, title: str, path: Path) -> None:
    """Depósito, clientes y una polilínea por ruta."""
    fig = Figure(figsize=(6, 6))
    ax = fig.subplots()
    xy = inst.coords
    for route in sol.routes:
        path_xy = xy[[0, *route.nodes, 0]]
        ax.plot(path_xy[:, 0], path_xy[:, 1], "-o", ms=3, lw=1)
    ax.plot(*xy[0], "ks", ms=9, label="depósito")
    ax.set_title(title, fontsize=10)
    ax.set_aspect("equal")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
