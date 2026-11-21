"""Aleatorización sesgada de BR-CWS (sección 5.2): distribución geométrica de parámetro p."""

import math
import random


def geometric_index(k: int, p: float, rng: random.Random) -> int:
    """Posición geométrica (0 = mejor arista) dentro de una lista de k aristas."""
    # 1 − u ∈ (0, 1]: evita log(0). El módulo devuelve las colas largas a la lista.
    return int(math.log(1 - rng.random()) / math.log(1 - p)) % k
