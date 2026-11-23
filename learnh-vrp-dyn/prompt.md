# Actualizar la presentación (`presentation/deck.html`)

Hemos cambiado el proyecto y la presentación ha quedado desfasada. Actualízala con lo que sigue. Mantén el idioma (inglés), el estilo y la estructura visual del deck; cambia solo el contenido que se indica.

## Qué ha cambiado

1. **Ya no hay v1 ni v2.** Hemos descartado la v1 (la réplica literal del paper). La antigua **v2 pasa a ser nuestro enfoque**: "our learnheuristic" / "D-BR-CWS (ours)". En ningún sitio del deck debe aparecer "v1", "v2" ni "v2 vs v1".
   - Nuestro enfoque = Algorithms 1 y 2 del paper (caja negra + caja blanca + BR-CWS dinámico) **más dos extensiones que el paper no tiene**:
     - **Los dos sentidos de cada unión:** Algorithm 2 predice `… i | j …` y `… j | i …` y guarda el ahorro del más barato. El paper no habla del sentido, y con costes que dependen de la carga, el sentido cambia el coste.
     - **Búsqueda local 2-opt** (mejor mejora) en cada ruta al acabar cada construcción, guiada por la caja blanca. La caja negra revela el coste real de las rutas que cambian.
2. **Versión con numba** (`src/dynamic/d_br_cws_numba.py`): el mismo algoritmo compilado con numba, con resultados idénticos (mismo DRC en las 30 instancias) y unas 2× más rápido.
3. **Experimento:** 5 semillas × 100 construcciones por semilla, `p = 0.2`. El paper usa 30 semillas y no dice cuántas construcciones. Quita cualquier mención a "30 seeds" como configuración nuestra.

## Diapositivas a cambiar

| Diapositiva actual | Qué hacer |
|---|---|
| Portada / subtítulo ("30 seeds per approach, best solution kept") | "5 seeds × 100 constructions per approach, best solution kept" |
| **Our Implementation** (tarjeta "v1 · FAITHFUL TO THE PAPER") | Una sola implementación: el paper más las dos extensiones. Añade una línea sobre la versión numba (mismos resultados, ~2× más rápida) |
| **What the Paper Leaves Open** | Fila "Merge direction": `not discussed` → `ours: the cheaper of both directions`. Fila "Runs": `5 seeds × 100 constructions, p = 0.2` (ya estaba) |
| **v1 vs v2** | Conviértela en **"What We Add to the Paper"**: columna Paper (una ruta unida por pareja, sin búsqueda local) frente a columna Ours (los dos sentidos + 2-opt) |
| **Why Direction Matters** | Se queda: justifica la primera extensión |
| **Our Results: Static vs Dynamic (v1)** | Pasa a **"Our Results vs the Paper"**, con los números de abajo |
| **Our Results: v2 vs v1** (incluida la tabla "WHERE THE GAIN COMES FROM · … VS v1" y "503 s vs 385 s") | **Elimínala.** En su lugar, una diapositiva **"Performance: with and without numba"** (tabla de abajo) |
| **Against the Best Known Solutions** | Solo dos series: Static (SRC) y Ours (DRC). Sustituye el gráfico SVG incrustado por `figures/plots/bks_gap.png`, que ya está regenerado |
| Conclusiones / limitaciones ("Ours: 3.5% (v1), 9.2% with v2", "our v2: −6%") | "Paper: static ~12% more expensive than dynamic. Ours: 10.3%. Forecasts exact (DFC ≈ DRC) in both". Sobre el sentido: "merge direction ignored by the paper, yet it changes the cost; we take the cheaper one" |

## Números (5 semillas, 30 instancias)

### Frente al paper: gap medio respecto al DRC

| | Ours | Paper |
|---|---:|---:|
| DFC | 0.00 % | 0.00 % |
| SRC | 10.27 % | 12.02 % |
| SFC | 13.53 % | −1.50 % (el artículo publica −1.25 %; −1.50 % es la media recalculada con sus costes) |
| DRC medio | 813.94 | 947.96 |
| SRC medio | 893.95 | 1066.32 |

- **SRC > DRC en las 30 instancias**, de 4.49 % (E-n33-k4) a 18.36 % (A-n38-k5): ignorar la dinámica sale caro, como en el paper.
- **DFC ≈ DRC:** la caja blanca aprende la caja negra casi exacta (`b0 ≈ 0.5`, `b1 ≈ 1`), igual que en el paper.
- **El SFC sale al revés que en el paper.** Con la ecuación (2) y `Q` = carga al salir de `i`, el coste real queda por debajo de la distancia (SRC/SFC entre 0.82 y 1.03). En el paper está entre 1.07 y 1.20: su caja negra cobra más, y el artículo no da detalle suficiente para saber por qué.
- **Costes absolutos:** nuestro DRC queda un 14.7 % por debajo del del paper, sobre todo por esa caja negra más barata. Solo se comparan en orden de magnitud.

Tabla por instancia y gráfico: `results/comparison_paper.csv` y `figures/plots/src_gap.png` (gap SRC vs DRC por instancia, paper frente a nuestro).

### Frente a la BKS (coste real de las rutas de la BKS con la misma caja negra)

| Gap medio | |
|---|---:|
| Static (SRC) | +6.59 % |
| Ours (DRC) | −3.32 % |

Nuestro enfoque baja del coste real de la BKS en **28 de 30** instancias (las excepciones son B-n67-k10, +0.93 %, y E-n22-k4, +0.23 %). El estático queda por encima en 28 de 30. Nota para la diapositiva: la BKS es óptima en distancia, no en carga.

### Rendimiento con y sin numba (dinámico, 5 semillas × 100 construcciones)

| Instancia | Clientes | Sin numba (s) | Con numba (s) | Speedup |
|---|---:|---:|---:|---:|
| E-n22-k4 | 21 | 2.49 | 0.90 | 2.8× |
| E-n30-k3 | 29 | 4.28 | 1.28 | 3.3× |
| A-n32-k5 | 31 | 4.06 | 1.53 | 2.7× |
| E-n51-k5 | 50 | 7.32 | 2.67 | 2.7× |
| A-n80-k10 | 79 | 19.17 | 8.54 | 2.2× |
| E-n101-k14 | 100 | 26.32 | 12.55 | 2.1× |
| F-n135-k7 | 134 | 70.77 | 33.05 | 2.1× |
| M-n200-k16 | 199 | 157.57 | 105.76 | 1.5× |
| **Total (30 instancias)** | | **503.9** | **248.7** | **2.0×** |

- Resultados idénticos: el mismo DRC en las 30 instancias.
- Qué compila numba: el Algorithm 2 (~70 % del tiempo) en un bucle sin arrays intermedios y con la predicción hecha a partir de los coeficientes de la caja blanca, y el 2-opt sobre una matriz de costes.
- El speedup baja con el tamaño, porque lo que sigue en Python (reconstruir y ordenar la lista de ahorros tras cada unión) crece con el número de parejas.
- Ejecución completa: estático 114 s, dinámico 504 s, dinámico con numba 249 s.

La tabla completa de las 30 instancias está en `results/learnheuristic.csv` (columnas `time_dynamic_s`, `time_dynamic_numba_s`, `speedup_numba`) y en el README, sección "Con y sin numba".

## Figuras disponibles (ya regeneradas)

- `figures/plots/src_gap.png`: gap SRC vs DRC por instancia, paper frente a nuestro.
- `figures/plots/bks_gap.png`: gap frente a la BKS, estático frente a nuestro.
- `figures/static/<inst>.png` y `figures/dynamic/<inst>.png`: rutas de la mejor solución. `figures/dynamic_v2/` ya no existe.

## Comprobación final

- Busca en el deck "v1", "v2", "30 seeds", "385 s", "503 s vs" y "3.5%": no debe quedar ninguno.
- Todas las cifras deben coincidir con las de este documento.
