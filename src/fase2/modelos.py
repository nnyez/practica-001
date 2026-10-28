"""
Constructores de modelos de series temporales.

Sigue el estilo del cuaderno de referencia ``RNN_LSTM.ipynb``:
una capa recurrente + densa de salida, pérdida MAE y optimizador Adam.
"""

from __future__ import annotations

from keras import Input, Sequential
from keras.layers import Dense, Dropout, LSTM, SimpleRNN


def construir_modelo(
    tipo: str = "lstm",
    n_pasos: int = 7,
    n_variables: int = 15,
    unidades: int = 50,
    dropout: float = 0.0,
) -> Sequential:
    """Construye un modelo recurrente según ``tipo``.

    - ``rnn``: SimpleRNN de una capa.
    - ``lstm``: LSTM de una capa.
    - ``lstm_apilada``: dos capas LSTM.
    """
    if tipo not in {"rnn", "lstm", "lstm_apilada"}:
        raise ValueError(f"tipo desconocido: {tipo}. Usa 'rnn', 'lstm' o 'lstm_apilada'.")

    modelo = Sequential([Input(shape=(n_pasos, n_variables))])

    if tipo == "rnn":
        modelo.add(SimpleRNN(unidades))
    elif tipo == "lstm":
        modelo.add(LSTM(unidades))
    else:
        modelo.add(LSTM(unidades, return_sequences=True))
        modelo.add(LSTM(unidades))

    if dropout > 0:
        modelo.add(Dropout(dropout))

    modelo.add(Dense(1))
    modelo.compile(loss="mae", optimizer="adam")
    return modelo
