"""Gap SRC frente a DRC por instancia: paper (tabla 1) y nuestra learnheuristic.

Como en la tabla 1 del paper: gap = (SRC − DRC) / DRC · 100 por instancia, y la
media es la media de esos gaps.

    python -m src.utils.plot_gaps   # → figures/plots/src_gap.png y tabla Markdown por pantalla
"""

import csv
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure

ROOT = Path(__file__).parents[2]

# columna "GAP w.r.t. DRC (%) · SRC" de la tabla 1, mismo orden que results/learnheuristic.csv
PAPER = [0.98, 15.63, 10.54, 9.12, 15.33, 15.90, 16.43, 16.78, 16.09, 12.15, 10.21, 23.58, 18.40, 13.92, 14.02,
         2.14, 3.96, 3.87, 9.77, 10.85, 14.71, 4.67, 14.47, 9.67, 8.71, 8.23, 15.43, 19.32, 10.73, 15.11]

rows = list(csv.DictReader(open(ROOT / "results" / "learnheuristic.csv")))
names = [r["instance"] for r in rows]
src = np.array([float(r["src"]) for r in rows])
drc = np.array([float(r["drc"]) for r in rows])
series = {"Paper (SRC vs DRC)": np.array(PAPER), "Nuestro (SRC vs DRC)": 100 * (src - drc) / drc}
assert len(PAPER) == len(names)

f = lambda v: f"{v:.2f}".replace(".", ",")  # noqa: E731
print("| Instancia | SRC | DRC | Paper (%) | Nuestro (%) |")
print("|---|---:|---:|---:|---:|")
for k, name in enumerate(names):
    print(f"| {name} | {f(src[k])} | {f(drc[k])} | " + " | ".join(f(g[k]) for g in series.values()) + " |")
print("| **Media** | | | " + " | ".join(f"**{f(g.mean())}**" for g in series.values()) + " |")

fig = Figure(figsize=(16, 6))
ax = fig.subplots()
x = np.arange(len(names))
width = 0.4
for k, (label, g) in enumerate(series.items()):
    ax.bar(x + (k - 0.5) * width, g, width, color=("#94a3b8", "#c84b31")[k], label=f"{label} · media {g.mean():.2f} %")
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(x, names, rotation=60, ha="right", fontsize=8)
ax.set_ylabel("gap SRC frente a DRC (%)")
ax.set_title("Cuánto más cuesta en real la solución estática que la dinámica: (SRC − DRC) / DRC", fontsize=10)
ax.grid(axis="y", alpha=0.3)
ax.legend(fontsize=9)
fig.tight_layout()
(ROOT / "figures" / "plots").mkdir(parents=True, exist_ok=True)
fig.savefig(ROOT / "figures" / "plots" / "src_gap.png", dpi=120)
