"""Experimento del paper (Tabla 1): enfoque estático frente a dinámico en las 30 instancias.

    python main.py                       # resuelve las 30
    python main.py A-n32-k5 E-n51-k5     # solo esas (sobrescribe el CSV solo con ellas)

- Estático: BR-CWS con distancias (lo que cree que cuesta, SFC). Después la caja
  negra revela lo que cuesta de verdad (SRC).
- Dinámico: learnheuristic (D-BR-CWS) con caja negra y caja blanca. Coste real
  (DRC) y el que predice la caja blanca (DFC).
- Dinámico v2: D-BR-CWS con los dos sentidos de unión y 2-opt (DRC v2, DFC v2).
Gaps respecto al DRC, como en la Tabla 1; los de v2, respecto al DRC v2.
"""

import sys
import time
from pathlib import Path

from src import cws
from src.dynamic import d_br_cws, d_br_cws_v2
from src.dynamic.black_box import BlackBox
from src.dynamic.white_box import WhiteBox
from src.static import br_cws
from src.utils import cvrplib
from src.utils.output import plot_solution, write_csv
from src.vrp_objects import Solution

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"

# Sección 5.2 del paper: p ∈ (0,1; 0,3). El paper usa 30 semillas y no dice cuántas iteraciones.
P = 0.2
N_ITER = 100  # construcciones por semilla, en cada enfoque
SEEDS = range(5)


def gap(cost: float, drc: float) -> float:
    return round(100 * (cost - drc) / drc, 2)


def build_solution(name: str) -> dict:
    """Una instancia: mejor solución estática y dinámica entre todas las semillas."""
    inst = cvrplib.read_instance(DATA_DIR / f"{name}.vrp")
    static: tuple[Solution, float] | None = None  # (solución, SRC); la mejor por SFC
    dynamic: tuple[Solution, float, WhiteBox] | None = None  # (solución, DFC, caja blanca); la mejor por DRC
    dynamic_v2: tuple[Solution, float] | None = None  # (solución, DFC v2); la mejor por DRC v2
    t_static = t_dynamic = t_dynamic_v2 = 0.0
    for seed in SEEDS:
        black_box = BlackBox(inst, seed)

        start = time.perf_counter()
        sol = br_cws.multi_start(inst, P, N_ITER, seed)
        t_static += time.perf_counter() - start
        cws.check(sol, inst)
        if static is None or sol.cost < static[0].cost:
            static = (sol, sum(black_box.get_real_cost(route) for route in sol.routes))

        white_box = WhiteBox(inst.capacity)
        start = time.perf_counter()
        sol = d_br_cws.multi_start(inst, P, N_ITER, seed, black_box, white_box)
        t_dynamic += time.perf_counter() - start
        cws.check(sol, inst, distances=False)
        if dynamic is None or sol.cost < dynamic[0].cost:
            dynamic = (sol, d_br_cws.forecast_cost(sol, white_box), white_box)

        white_box_v2 = WhiteBox(inst.capacity)
        start = time.perf_counter()
        sol = d_br_cws_v2.multi_start(inst, P, N_ITER, seed, BlackBox(inst, seed), white_box_v2)
        t_dynamic_v2 += time.perf_counter() - start
        cws.check(sol, inst, distances=False)
        if dynamic_v2 is None or sol.cost < dynamic_v2[0].cost:
            dynamic_v2 = (sol, d_br_cws.forecast_cost(sol, white_box_v2))
    assert static is not None and dynamic is not None and dynamic_v2 is not None

    (s_sol, src), (d_sol, dfc, white_box), (v2_sol, dfc_v2) = static, dynamic, dynamic_v2
    sfc, drc, drc_v2 = s_sol.cost, d_sol.cost, v2_sol.cost
    row = {
        "instance": name,
        "customers": inst.n_customers,
        "capacity": inst.capacity,
        "dfc": round(dfc, 2),
        "drc": round(drc, 2),
        "src": round(src, 2),
        "sfc": round(sfc, 2),
        "routes_dynamic": len(d_sol.routes),
        "routes_static": len(s_sol.routes),
        "gap_dfc_pct": gap(dfc, drc),
        "gap_src_pct": gap(src, drc),
        "gap_sfc_pct": gap(sfc, drc),
        "wb_b0": round(float(white_box.beta[0]), 4),
        "wb_b1": round(float(white_box.beta[1]), 4),
        "time_static_s": round(t_static, 2),
        "time_dynamic_s": round(t_dynamic, 2),
        "dfc_v2": round(dfc_v2, 2),
        "drc_v2": round(drc_v2, 2),
        "routes_dynamic_v2": len(v2_sol.routes),
        "gap_dfc_v2_pct": gap(dfc_v2, drc_v2),
        "gap_drc_v1_pct": gap(drc, drc_v2),
        "time_dynamic_v2_s": round(t_dynamic_v2, 2),
    }
    print(
        f"{name:<12} DFC {dfc:8.2f}  DRC {drc:8.2f}  SRC {src:8.2f}  SFC {sfc:8.2f}"
        f"  rutas {len(d_sol.routes):>2}/{len(s_sol.routes):>2}"
        f"  gaps {row['gap_dfc_pct']:5.2f} {row['gap_src_pct']:6.2f} {row['gap_sfc_pct']:6.2f} %"
        f"  {t_static:5.1f} s / {t_dynamic:5.1f} s"
        f"  | v2 DRC {drc_v2:8.2f} ({row['gap_drc_v1_pct']:5.2f} % mejor que v1)  {t_dynamic_v2:5.1f} s"
    )
    plot_solution(inst, s_sol, f"{name} · estático · SFC {sfc:.0f} · SRC {src:.0f}", FIGURES_DIR / "static" / f"{name}.png")
    plot_solution(inst, d_sol, f"{name} · dinámico · DRC {drc:.0f} · DFC {dfc:.0f}", FIGURES_DIR / "dynamic" / f"{name}.png")
    plot_solution(inst, v2_sol, f"{name} · dinámico v2 · DRC {drc_v2:.0f} · DFC {dfc_v2:.0f}", FIGURES_DIR / "dynamic_v2" / f"{name}.png")
    return row


def main() -> None:
    names = sys.argv[1:] or cvrplib.INSTANCES
    rows = [build_solution(name) for name in names]
    write_csv(rows, RESULTS_DIR / "learnheuristic.csv")
    for key in ("dfc", "src", "sfc"):
        print(f"gap medio {key.upper()} frente a DRC: {sum(r[f'gap_{key}_pct'] for r in rows) / len(rows):.2f} %")
    for key in ("dfc_v2", "drc_v1"):
        print(f"gap medio {key.upper()} frente a DRC v2: {sum(r[f'gap_{key}_pct'] for r in rows) / len(rows):.2f} %")


if __name__ == "__main__":
    main()
