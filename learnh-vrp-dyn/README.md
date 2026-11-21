# Learnheuristics en el VRP con entradas dinámicas

Arnau, Juan y Serra (2018). *On the Use of Learnheuristics in Vehicle Routing Optimization Problems with Dynamic Inputs*. Algorithms 11(12), 208. doi:10.3390/a11120208 — copia en [`paper.pdf`](paper.pdf).

Esta carpeta va por fases:

- **Fase 1 (hecha):** CVRP clásico con Clarke & Wright voraz.
- **Fase 2 (hecha):** BR-CWS, la misma construcción con elección geométrica, dentro de un multiarranque.
- **Fase 3 (hecha):** la learnheuristic del paper (caja negra + caja blanca + BR-CWS dinámico) y el experimento de la Tabla 1, estático frente a dinámico.

## El paper en un esquema

| Pieza | Qué es en el paper |
|---|---|
| Problema base | CVRP: depósito 0, clientes con demanda `d_i`, flota homogénea de capacidad `Q`, coste `c_ij` simétrico. Minimizar coste total |
| Lo dinámico | El coste real de una arista depende de la carga con la que sale el vehículo: se conoce solo al terminar la ruta |
| Caja negra (BB) | `c'_ij = c_ij · (1/2 + Q_ik / C + e)`, `e ~ U[-10⁻³, 10⁻³]`, `Q_ik` = carga al salir de `i` en la ruta `k`. Corrección entre ×½ (vacío) y ×1½ (lleno) |
| Caja blanca (WB) | Regresión lineal que aprende la BB con las rutas que se van completando y predice el coste de las rutas candidatas |
| Heurística constructiva | **BR-CWS**: CWS con elección aleatoria sesgada (geométrica, `p ∈ (0,1; 0,3)`) en la lista de ahorros |
| Metaheurística | Multiarranque: construir muchas soluciones BR-CWS y quedarse con la mejor |
| Ahorros dinámicos | En la versión dinámica la lista se recalcula tras cada unión: `s = coste real(Ri) + coste real(Rj) − coste predicho(Ri+Rj)`. Puede ser negativo (aquí esas uniones se descartan) |
| Comparación | Estático (ignora la BB al construir) frente a dinámico (usa la WB). Métricas: DFC, DRC, SFC, SRC (Dynamic/Static × Forecasted/Real Cost) |
| Resultado | SRC queda de media un **12 %** por encima de DRC; DFC ≈ DRC (la WB aprende enseguida porque la BB es lineal) |

Orden de construcción previsto:

```mermaid
flowchart LR
  A[CWS voraz<br/>fase 1] --> B[BR-CWS<br/>elección geométrica]
  B --> C[Multiarranque<br/>mejor de N]
  C --> D[Caja negra<br/>coste real por carga]
  D --> E[Caja blanca<br/>regresión lineal]
  E --> F[Estático vs dinámico<br/>DFC DRC SFC SRC]
```

## Datos

Las 30 instancias de la Tabla 1 del paper (conjuntos A, B, E, F, M, P de CVRPLIB, <https://galgos.inf.puc-rio.br/cvrplib>), ya descargadas en `data/`:

- `data/<nombre>.vrp`: instancia en formato TSPLIB (coordenadas, demandas, capacidad).
- `data/<nombre>.sol`: mejor solución conocida (BKS): rutas y coste.

Distancias: euclídeas **sin redondear**, como en el paper (los costes de su Tabla 1 tienen decimales: SFC de A-n32-k5 = 816,73). Las BKS de CVRPLIB usan la euclídea redondeada al entero (`EUC_2D` de TSPLIB), así que ya no se comparan con ellas.

## Estructura

| Ruta | Para qué sirve |
|---|---|
| `main.py` | Experimento de la Tabla 1: para cada instancia, enfoque estático y dinámico; comprueba, guarda CSV y figuras |
| `src/utils/cvrplib.py` | Lista de instancias del paper, lectura de `.vrp` y `.sol` |
| `src/utils/output.py` | Escritura del CSV y dibujo de rutas |
| `src/utils/biased_random.py` | `geometric_index`: posición aleatoria con distribución geométrica (BR-CWS) |
| `src/vrp_objects.py` | Clases `Node`, `Edge`, `Route` y `Solution` de las transparencias de CWS (`vrp_objects.py`) |
| `src/cws.py` | Piezas comunes de CWS con esas clases (nodos y arcos, ahorros, solución dummy, unión de rutas, arcos y cargas de una ruta) y comprobación de factibilidad |
| `src/static/g_cws.py` | CWS voraz: `build_vrp_sol` (Algorithm 1) cogiendo siempre la mejor arista. `python -m src.static.g_cws A-n80-k10` imprime la solución como en las transparencias |
| `src/static/br_cws.py` | BR-CWS: su propio `build_vrp_sol` con elección geométrica y el multiarranque `multi_start`. Es el enfoque estático |
| `src/dynamic/d_br_cws.py` | D-BR-CWS (v1): Algorithms 1 y 2 completos, con caja negra y caja blanca. Es el enfoque dinámico del paper |
| `src/dynamic/d_br_cws_v2.py` | D-BR-CWS v2: v1 con los dos sentidos de unión en Algorithm 2 y búsqueda local 2-opt |
| `src/dynamic/black_box.py` | Caja negra: ecuación (2), el coste real de una ruta |
| `src/dynamic/white_box.py` | Caja blanca: regresión lineal (`LinearRegression` de scikit-learn, sin término independiente) que aprende de la caja negra |
| `data/` | Instancias y BKS de CVRPLIB |
| `results/learnheuristic.csv` | Una fila por instancia, con las columnas de la Tabla 1 |
| `figures/static/`, `figures/dynamic/`, `figures/dynamic_v2/` | Rutas de la mejor solución de cada enfoque |

## Cómo se ejecuta

Todos los proyectos de `work-papers/` comparten el entorno `work-papers/.venv`. Desde esta carpeta:

```bash
source ../.venv/bin/activate
uv pip install -r requirements.txt   # solo la primera vez o si cambian las dependencias
python main.py                       # las 30
python main.py A-n32-k5 E-n51-k5     # solo algunas
```

## CWS clásico

Construcción de las transparencias de CWS (`cws_heuristic.py`, A. A. Juan) con las clases `Node`, `Edge`, `Route` y `Solution` de `src/vrp_objects.py`, ordenada como los Algorithm 1 y 2 del paper quitando la caja negra y la caja blanca. Las piezas comunes están en `src/cws.py`; el bucle del Algorithm 1 voraz, en `src/static/g_cws.py`:

| Paper | Código | Qué hace |
|---|---|---|
| `BUILDDVRPSOL` (Alg. 1) | `g_cws.build_vrp_sol(inst)` | Bucle principal |
| (lectura de nodos y arcos) | `vrp_objects.create_nodes_and_edges(inst)` | Un `Node` por fila con sus `Edge` depósito → nodo (`dn_edge`) y nodo → depósito (`nd_edge`); un `Edge` por pareja `i < j` (con su inverso), con coste y `s_ij = c_0i + c_0j − c_ij`, en `edges[i, j]` |
| `COMPUTESAVINGS` (Alg. 2) | `compute_savings(edges)` | `Savings`: filas `(i, j, s_ij)` en orden decreciente de ahorro. Es la misma lista que usan BR-CWS y D-BR-CWS |
| `generateBaseSolution` | `generate_base_solution(nodes)` | Solución dummy: una `Route` por cliente, `0 → i → 0` |
| `index ← generate random number` + `get edge` + `delete edge` | `edges[savings.get(0)]` + `savings.delete(0)` | Voraz: siempre la mejor arista que queda |
| `mergeFeasible(edge)` | `merge_feasible(edge, capacity)` | `checkMergingConditions`: rutas distintas, `i` y `j` exteriores (`is_interior`), demanda conjunta `≤ Q` |
| `mergeRoutes(edge, solution)` | `merge_routes(edge, solution)` | Orienta las rutas como `0 … i → 0` y `0 → j … 0` (`Route.reverse`), quita esos dos arcos al depósito y une `0 … i \| j … 0` |

Comprobación: el voraz da 1860,94 en A-n80-k10, con las mismas rutas que las transparencias, y reproduce los costes CWS de la tabla del JORS (A-n32-k5 843,69; A-n65-k9 1239,42…).

Las líneas 11-14 del Algorithm 1 (coste real, caja blanca y recálculo de ahorros) no existen en la versión clásica: el coste de una ruta es su distancia y la lista de ahorros no cambia.

## BR-CWS

`src/static/br_cws.py` tiene dos bucles:

1. **`br_cws.build_vrp_sol(inst, p, rng)`** construye una solución. Es el mismo Algorithm 1 que `g_cws.build_vrp_sol` y usa las mismas piezas de `cws.py`; solo cambia la línea 5. Por cada arista que saca, pide un número aleatorio `u` y lo convierte en posición con `geometric_index`: `int(log(1 − u) / log(1 − p)) % k`. La posición `k` sale con probabilidad proporcional a `p (1 − p)^k`: con `p → 1` se recupera el voraz y con `p → 0`, una elección uniforme.
2. **`multi_start(inst, p, n_iter, seed)`** es el multiarranque de la sección 4.1. Crea un generador con la semilla y llama `n_iter` veces a `br_cws.build_vrp_sol`. El generador avanza en cada llamada, así que cada iteración recibe números aleatorios distintos y construye otra solución. Empieza con la voraz y devuelve la mejor, así que nunca sale peor que CWS.

Referencia frente a la BKS, con la versión anterior de `main.py`: el voraz queda a un 4,86 % de media y BR-CWS (`p = 0,2`, 500 iteraciones, semilla 0) a un 2,02 %. Con distancias enteras hay muchos ahorros empatados; la ordenación es estable, así que entre empates va primero la pareja `(i, j)` de índices más bajos.

## Learnheuristic (D-BR-CWS)

`src/dynamic/d_br_cws.py` sigue los Algorithms 1 y 2 del paper línea a línea (los comentarios llevan el número de línea). El Algorithm 1 es literal, incluidos `delete edge` (línea 7) y el `if mergeFeasible` (línea 8). El Algorithm 2 hace las mismas cuentas con los nombres del paper (`exterior_nodes`, `i_real_cost`, `merged_predicted_cost`, `route_savings`), pero calcula todas las parejas a la vez con numpy en lugar de con dos bucles:

| Paper | Código | Qué hace |
|---|---|---|
| `BUILDDVRPSOL` (Alg. 1) | `d_br_cws.build_vrp_sol(inst, p, rng, black_box, white_box)` | Construye una solución |
| `generateBaseSolution(inputs)` (l. 2) | `d_br_cws.generate_base_solution(nodes, black_box)` | Solución dummy `0 → i → 0`, con el coste real de cada ruta (lo que lee `getCost ▷ Black Box` en Alg. 2) |
| `blackBox.getRealCost(route)` (l. 11) | `BlackBox.get_real_cost(route)` | `Σ c_e (1/2 + Q_e / C + ϵ)`, con `ϵ ~ U[−10⁻³, 10⁻³]` nuevo en cada arco y llamada |
| `solution.update(realCost)` (l. 12) | `Solution.update(route, real_cost)` | El coste de la ruta pasa a ser el real |
| `whiteBox.update(route, realCost)` (l. 13) | `WhiteBox.update(dist, w, real_cost)` | Añade una observación y reajusta la regresión |
| `computeSavings(solution, whiteBox)` (Alg. 2, l. 3 y 14) | `d_br_cws.compute_savings(solution, white_box)` | `coste real(A) + coste real(B) − predicción(A … i \| j … B)` para cada pareja de nodos exteriores; la lista guarda la pareja `(i, j)` y su `Edge` se busca al sacarla (línea 6) |
| `mergeRoutes(iRoute, jRoute)` + `whiteBox.predictCost(mergedRoute)` (Alg. 2, l. 8 y 11) | `d_br_cws.merge_routes(i_route, j_route)` + `WhiteBox.predict_cost(dist, w)` | `b0 · Σ c_e + b1 · Σ c_e Q_e / C` de la ruta unida, sin construirla |
| Multiarranque (4.1) | `d_br_cws.multi_start(...)` | La mejor por coste real de `n_iter` construcciones; la caja blanca sigue aprendiendo entre ellas |

Decisiones donde el paper no entra en detalle:

- **Carga `Q_e`.** Es reparto: el vehículo sale lleno con la carga de la ruta, deja la demanda en cada cliente y vuelve vacío. Se define en un solo sitio, `cws.edge_loads(route)`, que usan la caja negra y la caja blanca (`d_br_cws.route_features`). Por eso recorrer una ruta en un sentido o en el otro no cuesta lo mismo.
- **Sentido de la unión.** Con costes que dependen de la carga, `… i | j …` y `… j | i …` cuestan distinto. Como en el paper, Algorithm 2 predice una sola ruta unida por pareja `i < j`, `… i | j …`, y `merge_routes` la deja en ese sentido aunque el contrario fuera más barato. v2 lo cambia.
- **Variables de la caja blanca.** El paper se queda con la carga y la capacidad. Aquí entran como `Q_e / C` en cada arco, ponderadas por su coste medio: `coste ≈ b0 · Σ c_e + b1 · Σ c_e Q_e / C`. Los valores verdaderos son `b0 = 1/2` y `b1 = 1`, y la regresión los encuentra (columnas `wb_b0`, `wb_b1`).
- **Datos de la caja blanca.** Como en el Algorithm 1, solo aprende de las rutas unidas (línea 13); las `0 → i → 0` de la solución base no son observaciones. Deja de actualizarse a las 500 observaciones (sección 5.2). Antes de tener datos (al empezar la primera construcción del multiarranque) predice la distancia.
- **Ahorros.** Solo se guardan los positivos, como en CWS clásico (el paper los guarda todos). Las uniones no factibles se quedan en la lista y las descarta la línea 8 del Algorithm 1, como en el paper.
- **Rapidez.** Algorithm 2 sigue el paper línea a línea, pero sin los dos bucles: `get_exterior_nodes` devuelve los `Node` extremos de ruta, `Routes.of` pasa sus `node.in_route` a columnas (carga, coste real, `Σ c_e` y `Σ c_e Q_e` en los dos sentidos), `get_route` da `i_route`/`j_route` en las posiciones de cada pareja, y `merge_routes` da `(Σ c_e, Σ c_e Q_e)` de la ruta unida en O(1) por pareja. Numpy hace todas las parejas a la vez.

## D-BR-CWS v2

`src/dynamic/d_br_cws_v2.py` reutiliza todo lo de v1 (caja negra, caja blanca, solución base, `Routes`, `merge_routes` de Alg. 2, multiarranque) y cambia dos cosas que el paper no tiene:

| | v1 (paper) | v2 |
|---|---|---|
| Algorithm 2 | Predice solo `… i \| j …` | Predice `… i \| j …` y `… j \| i …` (la misma ruta al revés: `Σ c_e Q'_e = Q · Σ c_e − Σ c_e Q_e`) y guarda el ahorro del sentido más barato. La lista guarda el arco en ese sentido (`i → j` o `j → i`) y `cws.merge_routes` deja la ruta así |
| Después de construir | Nada | `local_search`: 2-opt con mejor mejora en cada ruta, según el coste que predice la caja blanca, hasta que ningún movimiento lo baja. Invertir la ruta entera cuenta como movimiento. La caja negra revela el coste real de las rutas que cambian (`solution.update`) y la caja blanca aprende de ellas |
| Coste por construcción | — | ~1,3× v1 (503 s frente a 385 s en las 30 instancias) |

La búsqueda local usa la caja blanca y no la negra porque, como en el paper, el coste real solo se conoce al ejecutar la ruta; con `DFC ≈ DRC` la predicción basta para elegir.

## Experimento (Tabla 1)

Por cada instancia y semilla, los tres enfoques con el mismo `p` y el mismo número de construcciones:

- **Estático:** `br_cws.multi_start` con distancias. Su coste previsto es la distancia (SFC); la caja negra revela el real (SRC). Entre semillas se queda la de menor SFC, que es lo único que ve este enfoque.
- **Dinámico (v1):** `d_br_cws.multi_start`. Coste real (DRC) y el que predice la caja blanca al final (DFC). Entre semillas se queda la de menor DRC.
- **Dinámico v2:** `d_br_cws_v2.multi_start`, con su propia caja blanca y caja negra por semilla. DRC v2 y DFC v2, igual que v1.

Gaps respecto al DRC, como en el paper; los de v2, respecto al DRC v2. Parámetros en `main.py`: `P = 0.2`, `N_ITER = 100` construcciones por semilla, `SEEDS = range(5)`. El paper usa 30 semillas y no dice cuántas construcciones.

## Resultados

`results/learnheuristic.csv`. Ejecución completa: unos 17 min (estático 110 s, v1 385 s, v2 503 s; M-n200-k16: 44 s, 132 s y 153 s).

### Estático frente a dinámico (v1)

| Gap medio frente a DRC | Aquí | Paper |
|---|---:|---:|
| DFC | 0,00 % | 0,00 % |
| SRC | 3,52 % | 12,02 % |
| SFC | 6,61 % | −1,25 % |

- **DFC ≈ DRC.** La caja blanca aprende la caja negra casi exacta (`b0 ≈ 0,5`, `b1 ≈ 1`), porque es lineal y con poco ruido. Igual que en el paper.
- **SRC > DRC en 27 de 30 instancias.** Ignorar la dinámica sale caro, hasta un 10,6 % (A-n38-k5). En A-n65-k9, E-n33-k4 y M-n101-k10 el estático sale hasta un 1,6 % mejor: v1 une siempre en sentido `… i | j …` (como el paper) aunque el contrario sea más barato. v2 lo corrige (abajo).
- **SFC por encima del DRC, al revés que en el paper.** Con la ecuación (2) y `Q` = carga al salir de `i` ya servido, un arco cuesta `1/2 + Q/C` veces su distancia y la carga media por arco queda por debajo de `C/2`: el coste real sale por debajo de la distancia (SRC/SFC entre 0,82 y 1,03). En la Tabla 1 del paper SRC/SFC está entre 1,07 y 1,20, así que su caja negra cobra más; el artículo no da detalle suficiente para saber cómo (orientación de las rutas o definición exacta de `Q`).
- **Costes absolutos.** Las distancias son euclídeas sin redondear, como en el paper, pero las soluciones dependen de la semilla y del número de construcciones, así que los costes solo se comparan en orden de magnitud.

### Resumen: coste real de cada solución

Coste real (el que revela la caja negra) de la mejor solución de cada enfoque. Diferencias respecto al enfoque anterior (negativo = más barato): `v1 vs estático = (DRC v1 − SRC) / SRC`, `v2 vs v1 = (DRC v2 − DRC v1) / DRC v1`.

| Instancia | C | SRC (estático) | DRC v1 | DRC v2 | Rutas est. / v1 / v2 | v1 vs estático (%) | v2 vs v1 (%) |
|---|---:|---:|---:|---:|:---:|---:|---:|
| A-n32-k5 | 100 | 804,88 | 756,98 | 696,00 | 5 / 5 / 5 | -5,95 | -8,06 |
| A-n38-k5 | 100 | 750,24 | 678,12 | 633,87 | 5 / 6 / 6 | -9,61 | -6,53 |
| A-n55-k9 | 100 | 1076,54 | 1037,98 | 981,93 | 9 / 11 / 10 | -3,58 | -5,40 |
| A-n60-k9 | 100 | 1347,85 | 1313,46 | 1250,78 | 9 / 11 / 10 | -2,55 | -4,77 |
| A-n61-k9 | 100 | 1042,90 | 1013,08 | 954,35 | 10 / 11 / 11 | -2,86 | -5,80 |
| A-n65-k9 | 100 | 1176,38 | 1179,99 | 1091,86 | 9 / 12 / 9 | 0,31 | -7,47 |
| A-n80-k10 | 100 | 1804,56 | 1775,78 | 1664,08 | 10 / 10 / 11 | -1,59 | -6,29 |
| B-n35-k5 | 100 | 916,92 | 885,32 | 855,97 | 5 / 6 / 6 | -3,45 | -3,32 |
| B-n50-k7 | 100 | 717,96 | 703,94 | 669,78 | 7 / 8 / 8 | -1,95 | -4,85 |
| B-n52-k7 | 100 | 765,98 | 701,14 | 671,66 | 7 / 7 / 7 | -8,46 | -4,20 |
| B-n64-k9 | 100 | 852,13 | 838,24 | 814,88 | 10 / 11 / 10 | -1,63 | -2,79 |
| B-n67-k10 | 100 | 1032,75 | 1012,19 | 963,75 | 10 / 11 / 11 | -1,99 | -4,79 |
| B-n78-k10 | 100 | 1246,99 | 1213,18 | 1141,41 | 10 / 12 / 11 | -2,71 | -5,92 |
| E-n101-k14 | 112 | 1090,01 | 1076,36 | 993,85 | 14 / 17 / 15 | -1,25 | -7,67 |
| E-n22-k4 | 6000 | 386,28 | 357,43 | 334,00 | 4 / 5 / 4 | -7,47 | -6,56 |
| E-n23-k3 | 4500 | 463,94 | 451,42 | 434,66 | 3 / 4 / 3 | -2,70 | -3,71 |
| E-n30-k3 | 4500 | 462,85 | 458,46 | 418,89 | 4 / 4 / 4 | -0,95 | -8,63 |
| E-n33-k4 | 8000 | 805,77 | 818,52 | 771,15 | 4 / 4 / 4 | 1,58 | -5,79 |
| E-n51-k5 | 160 | 544,45 | 504,84 | 473,53 | 5 / 8 / 6 | -7,28 | -6,20 |
| E-n76-k10 | 140 | 884,47 | 821,61 | 759,58 | 10 / 14 / 11 | -7,11 | -7,55 |
| E-n76-k14 | 100 | 1023,32 | 996,26 | 925,86 | 15 / 18 / 16 | -2,64 | -7,07 |
| F-n135-k7 | 2210 | 1168,47 | 1156,37 | 1060,34 | 7 / 10 / 9 | -1,04 | -8,30 |
| M-n101-k10 | 200 | 810,71 | 818,87 | 760,78 | 10 / 10 / 10 | 1,01 | -7,09 |
| M-n200-k16 | 200 | 1349,81 | 1318,36 | 1202,22 | 17 / 22 / 18 | -2,33 | -8,81 |
| P-n22-k8 | 3000 | 561,98 | 551,84 | 533,57 | 9 / 9 / 9 | -1,80 | -3,31 |
| P-n40-k5 | 140 | 475,62 | 432,70 | 403,26 | 5 / 6 / 6 | -9,02 | -6,80 |
| P-n50-k10 | 100 | 687,86 | 674,29 | 624,60 | 11 / 12 / 11 | -1,97 | -7,37 |
| P-n55-k15 | 70 | 933,05 | 896,31 | 859,64 | 16 / 17 / 17 | -3,94 | -4,09 |
| P-n65-k10 | 130 | 801,05 | 771,86 | 721,31 | 10 / 12 / 11 | -3,64 | -6,55 |
| P-n70-k10 | 135 | 832,90 | 809,72 | 750,56 | 11 / 13 / 12 | -2,78 | -7,31 |
| **Media** | | | | | | **-3,31** | **-6,10** |

### Dinámico v1 frente a v2

La Tabla 1 del paper con v2 en lugar del estático: v1 ya mejora al estático, así que aquí se compara con v1. Gaps respecto al DRC v2 (positivo = v2 mejor).

| Instancia | Clientes | C | DFC v2 | DRC v2 | DRC v1 | Rutas v2 | Rutas v1 | DFC v2 vs DRC v2 (%) | DRC v1 vs DRC v2 (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A-n32-k5 | 31 | 100 | 695,99 | 696,00 | 756,98 | 5 | 5 | -0,00 | 8,76 |
| A-n38-k5 | 37 | 100 | 633,85 | 633,87 | 678,12 | 6 | 6 | -0,00 | 6,98 |
| A-n55-k9 | 54 | 100 | 981,90 | 981,93 | 1037,98 | 10 | 11 | -0,00 | 5,71 |
| A-n60-k9 | 59 | 100 | 1250,54 | 1250,78 | 1313,46 | 10 | 11 | -0,02 | 5,01 |
| A-n61-k9 | 60 | 100 | 954,33 | 954,35 | 1013,08 | 11 | 11 | -0,00 | 6,15 |
| A-n65-k9 | 64 | 100 | 1091,97 | 1091,86 | 1179,99 | 9 | 12 | 0,01 | 8,07 |
| A-n80-k10 | 79 | 100 | 1664,10 | 1664,08 | 1775,78 | 11 | 10 | 0,00 | 6,71 |
| B-n35-k5 | 34 | 100 | 856,15 | 855,97 | 885,32 | 6 | 6 | 0,02 | 3,43 |
| B-n50-k7 | 49 | 100 | 669,75 | 669,78 | 703,94 | 8 | 8 | -0,01 | 5,10 |
| B-n52-k7 | 51 | 100 | 671,74 | 671,66 | 701,14 | 7 | 7 | 0,01 | 4,39 |
| B-n64-k9 | 63 | 100 | 815,05 | 814,88 | 838,24 | 10 | 11 | 0,02 | 2,87 |
| B-n67-k10 | 66 | 100 | 963,99 | 963,75 | 1012,19 | 11 | 11 | 0,02 | 5,03 |
| B-n78-k10 | 77 | 100 | 1141,32 | 1141,41 | 1213,18 | 11 | 12 | -0,01 | 6,29 |
| E-n101-k14 | 100 | 112 | 993,82 | 993,85 | 1076,36 | 15 | 17 | -0,00 | 8,30 |
| E-n22-k4 | 21 | 6000 | 334,03 | 334,00 | 357,43 | 4 | 5 | 0,01 | 7,02 |
| E-n23-k3 | 22 | 4500 | 434,82 | 434,66 | 451,42 | 3 | 4 | 0,04 | 3,86 |
| E-n30-k3 | 29 | 4500 | 418,91 | 418,89 | 458,46 | 4 | 4 | 0,01 | 9,45 |
| E-n33-k4 | 32 | 8000 | 771,20 | 771,15 | 818,52 | 4 | 4 | 0,01 | 6,14 |
| E-n51-k5 | 50 | 160 | 473,54 | 473,53 | 504,84 | 6 | 8 | 0,00 | 6,61 |
| E-n76-k10 | 75 | 140 | 759,67 | 759,58 | 821,61 | 11 | 14 | 0,01 | 8,17 |
| E-n76-k14 | 75 | 100 | 925,87 | 925,86 | 996,26 | 16 | 18 | 0,00 | 7,60 |
| F-n135-k7 | 134 | 2210 | 1060,36 | 1060,34 | 1156,37 | 9 | 10 | 0,00 | 9,06 |
| M-n101-k10 | 100 | 200 | 760,85 | 760,78 | 818,87 | 10 | 10 | 0,01 | 7,64 |
| M-n200-k16 | 199 | 200 | 1202,20 | 1202,22 | 1318,36 | 18 | 22 | -0,00 | 9,66 |
| P-n22-k8 | 21 | 3000 | 533,60 | 533,57 | 551,84 | 9 | 9 | 0,01 | 3,42 |
| P-n40-k5 | 39 | 140 | 403,20 | 403,26 | 432,70 | 6 | 6 | -0,02 | 7,30 |
| P-n50-k10 | 49 | 100 | 624,64 | 624,60 | 674,29 | 11 | 12 | 0,01 | 7,95 |
| P-n55-k15 | 54 | 70 | 859,55 | 859,64 | 896,31 | 17 | 17 | -0,01 | 4,27 |
| P-n65-k10 | 64 | 130 | 721,24 | 721,31 | 771,86 | 11 | 12 | -0,01 | 7,01 |
| P-n70-k10 | 69 | 135 | 750,55 | 750,56 | 809,72 | 12 | 13 | -0,00 | 7,88 |
| **Media** | | | | | | | | **0,00** | **6,53** |

- **v2 gana en las 30 instancias**, entre un 2,9 % (B-n64-k9) y un 9,7 % (M-n200-k16); de media un 6,53 %. Las ganancias más grandes salen en las instancias grandes, donde las rutas son más largas y el sentido pesa más.
- **Menos rutas** en 16 instancias (una más solo en A-n80-k10): elegir el sentido barato hace rentables uniones que en v1 tenían ahorro negativo.
- **DFC v2 ≈ DRC v2.** La caja blanca predice igual de bien: 2-opt y los dos sentidos no cambian el modelo, solo lo usan más.

### SRC frente a DRC: paper, v1 y v2

`python -m src.utils.plot_gaps` → `figures/plots/src_gap.png` y tabla por instancia. Mismo cálculo que la tabla 1 del paper, `gap = (SRC − DRC) / DRC` por instancia y media de esos gaps; para v2 el DRC es el de v2.

| Gap medio SRC vs DRC | |
|---|---:|
| Paper | 12,02 % |
| Nuestro v1 | 3,52 % |
| Nuestro v2 | 10,27 % |

v2 deja el estático por encima en las 30 instancias (de 4,49 % en E-n33-k4 a 18,36 % en A-n38-k5); v1, en 27 de 30.

### Frente a la BKS (comparación dinámica)

`python -m src.utils.plot_bks` → `figures/plots/bks_gap.png`. Las rutas de la BKS de CVRPLIB (`data/*.sol`) pasan por la misma caja negra que nuestras soluciones, cada una en su sentido más barato, y se comparan con el coste real de cada enfoque: `gap = (coste − BKS) / BKS`, negativo = mejor que la BKS. La BKS está optimizada para distancia, no para carga: es una buena referencia, no el óptimo del problema dinámico.

| Gap medio frente al coste real de la BKS | |
|---|---:|
| Estático (SRC) | 6,59 % |
| D-BR-CWS v1 (DRC) | 2,98 % |
| D-BR-CWS v2 (DRC v2) | −3,32 % |

- **v2 baja del coste real de la BKS en 28 de 30 instancias** (no en B-n67-k10, +0,93 %, ni en E-n22-k4, +0,23 %): tener en cuenta la carga compensa más que partir de las mejores rutas en distancia.
- **v1 queda por encima** en 25 de 30, y el estático en 28 de 30.
