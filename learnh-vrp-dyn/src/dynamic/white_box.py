"""Caja blanca (WB, sección 4.2): regresión lineal que predice el coste real de una ruta.

Aprende online de lo que revela la caja negra (Algorithm 1, línea 13) y predice
el coste de las rutas unidas antes de unirlas (Algorithm 2, línea 11).
"""

import numpy as np
from sklearn.linear_model import LinearRegression

# Sección 5.2: con unas 500 observaciones el modelo ya es preciso; a partir de
# ahí deja de actualizarse para ahorrar tiempo.
MAX_DATA = 500


class WhiteBox:
    """coste real ≈ b0 · Σ c_e + b1 · Σ c_e Q_e / C, sumando sobre los arcos e de la ruta.

    El paper se queda con dos variables relevantes, la carga y la capacidad del
    vehículo; aquí entran como Q_e / C en cada arco, ponderadas por su coste
    medio c_e. Si la caja negra es la ecuación (2), los valores verdaderos son
    b0 = 1/2 y b1 = 1.

    `LinearRegression` de scikit-learn sin término independiente, reajustada con
    todos los datos en cada actualización. Antes de tener datos, (b0, b1) = (1, 0):
    el coste es la distancia, como en el enfoque estático.
    """

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.model = LinearRegression(fit_intercept=False)
        self.x: list[list[float]] = []
        self.y: list[float] = []
        self.beta = np.array([1.0, 0.0])

    def update(self, dist: float, w: float, real_cost: float) -> None:
        if len(self.y) >= MAX_DATA:
            return
        self.x.append([dist, w / self.capacity])
        self.y.append(real_cost)
        if len(self.y) >= 2:
            self.model.fit(self.x, self.y)
            self.beta = self.model.coef_

    def predict_cost(self, dist: np.ndarray, w: np.ndarray) -> np.ndarray:
        """dist = Σ c_e y w = Σ c_e Q_e de cada ruta: una predicción por ruta."""
        if len(self.y) < 2:
            return dist
        return self.model.predict(np.column_stack([dist, w / self.capacity]))
