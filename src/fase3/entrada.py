"""
Construcción de la ventana de entrada para un producto y una fecha.

Toma los 7 días anteriores a la fecha objetivo y arma la matriz
``(ventana, variables)`` en el mismo orden que usó el entrenamiento:
objetivo, variables temporales y one-hot del producto.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def _codificar_dia(dia_semana: int) -> tuple[float, float]:
    """Codifica el día de la semana como seno/coseno (ciclo de 7 días)."""
    angulo = 2 * np.pi * dia_semana / 7
    return float(np.sin(angulo)), float(np.cos(angulo))


def construir_ventana(
    df: pd.DataFrame, producto_id: str, fecha, ventana: int = config.VENTANA
) -> np.ndarray:
    """Devuelve la ventana ``(ventana, variables)`` para predecir ``fecha``."""
    producto_id = str(producto_id)
    fecha = pd.to_datetime(fecha)

    historial = df[df["product_id"] == producto_id].sort_values("fecha_venta")
    if historial.empty:
        raise ValueError(f"Producto '{producto_id}' no encontrado en los datos.")

    previos = historial[historial["fecha_venta"] < fecha]
    if len(previos) < ventana:
        raise ValueError(
            f"Se requieren {ventana} días de historial para {producto_id} "
            f"antes de {fecha.date()}; solo hay {len(previos)}."
        )

    ultimos = previos.tail(ventana)
    productos = sorted(df["product_id"].unique())
    posicion = productos.index(producto_id)

    X = np.zeros((ventana, 5 + len(productos)), dtype="float32")
    for i, fila in enumerate(ultimos.itertuples()):
        dia_sin, dia_cos = _codificar_dia(int(fila.dia_semana))
        X[i, 0] = fila.cantidad_vendida
        X[i, 1] = fila.es_fin_de_semana
        X[i, 2] = fila.es_feriado
        X[i, 3] = dia_sin
        X[i, 4] = dia_cos
        X[i, 5 + posicion] = 1.0
    return X


def ventana_disponible(df: pd.DataFrame, producto_id: str, fecha) -> bool:
    """Indica si hay historial suficiente para construir la ventana."""
    try:
        construir_ventana(df, producto_id, fecha)
        return True
    except ValueError:
        return False
