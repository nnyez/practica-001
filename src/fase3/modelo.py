"""
Carga del modelo LSTM y del escalador guardados durante el entrenamiento.

No se reconstruye nada a partir de los datos: el escalador se carga tal cual
se ajustó en train, que es lo correcto para desplegar.
"""

from __future__ import annotations

import joblib
import numpy as np

from . import config

_modelo = None
_escalador = None


def cargar_modelo() -> None:
    """Carga el modelo y el escalador (idempotente)."""
    global _modelo, _escalador
    if _modelo is not None:
        return

    if not config.RUTA_ESCALADOR.exists():
        raise FileNotFoundError(
            f"No se encontró el escalador en {config.RUTA_ESCALADOR}. "
            "Ejecuta primero el entrenamiento: python -m src.fase2.ejecutar"
        )

    import tensorflow as tf

    _modelo = tf.keras.models.load_model(config.RUTA_MODELO)
    _escalador = joblib.load(config.RUTA_ESCALADOR)


def predecir_ventana(X: np.ndarray) -> float:
    """Predice una ventana ``(días, variables)`` y devuelve unidades reales."""
    cargar_modelo()

    X = _escalador.transform(np.asarray(X, dtype="float32"))
    n_pasos, n_variables = X.shape
    prediccion = float(_modelo.predict(X.reshape(1, n_pasos, n_variables), verbose=0).ravel()[0])

    dummy = np.zeros((1, _escalador.n_features_in_), dtype="float32")
    dummy[0, 0] = prediccion
    return float(_escalador.inverse_transform(dummy)[0, 0])
