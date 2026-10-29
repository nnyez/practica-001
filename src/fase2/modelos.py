"""
Constructor del modelo de series temporales.

Sigue el estilo del cuaderno de referencia ``RNN_LSTM.ipynb``:
una capa LSTM de 50 unidades + densa de salida, pérdida MAE y
optimizador Adam. Es el único modelo entregado en la práctica.
"""

from __future__ import annotations

from keras import Input, Sequential
from keras.layers import Dense, LSTM


def construir_modelo(
    n_pasos: int = 7,
    n_variables: int = 15,
    unidades: int = 50,
) -> Sequential:
    """Construye el modelo LSTM (red neuronal recurrente) entregado."""
    modelo = Sequential([Input(shape=(n_pasos, n_variables))])
    modelo.add(LSTM(unidades))
    modelo.add(Dense(1))
    modelo.compile(loss="mae", optimizer="adam")
    return modelo
