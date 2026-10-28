"""
Funciones públicas de predicción.

- ``predecir_venta(producto_id, fecha)`` -> float
- ``predecir_batch(productos, fecha)`` -> list[dict]
"""

from __future__ import annotations

import pandas as pd

from . import config
from .entrada import construir_ventana
from .modelo import cargar_modelo, predecir_ventana

_datos: pd.DataFrame | None = None


def inicializar() -> None:
    """Carga el modelo y el historial en memoria (opcional, se hace solo)."""
    global _datos
    cargar_modelo()
    if _datos is None:
        _datos = pd.read_csv(config.RUTA_DATOS, encoding="utf-8-sig", parse_dates=["fecha_venta"])


def _historial() -> pd.DataFrame:
    """Devuelve el historial de ventas, cargándolo la primera vez."""
    if _datos is None:
        inicializar()
    return _datos


def predecir_venta(producto_id: str, fecha) -> float:
    """Predicción de demanda para un producto en una fecha (unidades reales)."""
    ventana = construir_ventana(_historial(), producto_id, fecha)
    return predecir_ventana(ventana)


def predecir_batch(productos: list, fecha) -> list[dict]:
    """Predicciones para varios productos en la misma fecha.

    Si un producto falla, se devuelve su entrada con la clave ``error`` sin
    interrumpir el resto del lote.
    """
    fecha = pd.to_datetime(fecha)
    resultados = []

    for producto_id in productos:
        try:
            prediccion = predecir_venta(str(producto_id), fecha)
            resultados.append({
                "producto_id": str(producto_id),
                "fecha": str(fecha.date()),
                "prediccion": round(prediccion, 2),
            })
        except Exception as exc:  # noqa: BLE001 - se reporta y se continúa
            resultados.append({
                "producto_id": str(producto_id),
                "fecha": str(fecha.date()),
                "error": str(exc),
            })

    return resultados
