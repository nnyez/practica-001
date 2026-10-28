"""
Evaluación y visualizaciones de los modelos.

Calcula RMSE / MAE / MAPE en unidades reales (tras desescalar) e incluye la
línea de persistencia (venta del día anterior) como baseline.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


def metricas(y_real: np.ndarray, y_pred: np.ndarray) -> dict:
    """RMSE, MAE y MAPE sobre valores en escala original."""
    rmse = float(np.sqrt(mean_squared_error(y_real, y_pred)))
    mae = float(mean_absolute_error(y_real, y_pred))
    mape = float(np.mean(np.abs((y_real - y_pred) / np.maximum(np.abs(y_real), 1e-8))) * 100)
    return {"RMSE": rmse, "MAE": mae, "MAPE_%": mape}


def predecir(modelo, X: np.ndarray) -> np.ndarray:
    """Predicciones del modelo como arreglo 1D (escala 0-1)."""
    return np.asarray(modelo.predict(X, verbose=0)).ravel()


def baseline_persistencia(X: np.ndarray) -> np.ndarray:
    """Venta del día inmediatamente anterior (último paso de la ventana)."""
    return X[:, -1, 0].ravel()


def desescalar(valores: np.ndarray, escalador, n_variables: int) -> np.ndarray:
    """Devuelve la columna objetivo a su escala original.

    El escalador se ajustó sobre todas las variables, así que se reconstruye
    una fila con la predicción en la primera posición (la columna objetivo).
    """
    valores = np.asarray(valores).reshape(-1, 1)
    dummy = np.zeros((valores.shape[0], n_variables), dtype="float32")
    dummy[:, 0] = valores[:, 0]
    return escalador.inverse_transform(dummy)[:, 0]


# --------------------------------------------------------------------------- #
# Figuras
# --------------------------------------------------------------------------- #
def graficar_curvas(historial, ruta=None):
    """Pérdida de entrenamiento y validación por época."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(historial.history["loss"], label="Entrenamiento")
    ax.plot(historial.history["val_loss"], label="Validación")
    ax.set_title("Pérdida (MAE) durante el entrenamiento")
    ax.set_xlabel("Época")
    ax.set_ylabel("MAE (ventas escaladas)")
    ax.legend()
    ax.grid(alpha=0.3)
    _guardar(fig, ruta)
    return fig


def graficar_predicciones(fechas, y_real, y_pred, ruta=None):
    """Serie temporal real vs predicción sobre el conjunto de prueba."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(fechas, y_real, label="Real", linewidth=2)
    ax.plot(fechas, y_pred, label="Predicción", linewidth=2, alpha=0.8)
    ax.set_title("Ventas diarias reales vs predicción (conjunto de prueba)")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Cantidad vendida (unidades)")
    ax.legend()
    ax.grid(alpha=0.3)
    _guardar(fig, ruta)
    return fig


def graficar_comparacion(resumen: pd.DataFrame, ruta=None):
    """Barras de RMSE por modelo, incluida la línea de persistencia."""
    fig, ax = plt.subplots(figsize=(8, 5))
    orden = resumen.sort_values("RMSE")
    colores = ["#2e7d32" if m.startswith("Baseline") else "#1565c0" for m in orden["modelo"]]
    barras = ax.bar(orden["modelo"], orden["RMSE"], color=colores)
    for barra, valor in zip(barras, orden["RMSE"]):
        ax.text(barra.get_x() + barra.get_width() / 2, valor, f"{valor:.1f}",
                ha="center", va="bottom", fontsize=10)
    ax.set_title("RMSE por modelo (unidades reales, conjunto de prueba)")
    ax.set_xlabel("Modelo")
    ax.set_ylabel("RMSE")
    ax.tick_params(axis="x", rotation=15)
    ax.grid(axis="y", alpha=0.3)
    _guardar(fig, ruta)
    return fig


def graficar_por_producto(df_producto: pd.DataFrame, ruta=None):
    """Real vs predicción para un producto concreto."""
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(df_producto["fecha"], df_producto["real"], label="Real", marker="o", markersize=4)
    ax.plot(df_producto["fecha"], df_producto["pred"], label="Predicción", marker="x", markersize=4)
    ax.set_title(f"{df_producto['nombre'].iloc[0]} - Real vs predicción (test)")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Cantidad vendida (unidades)")
    ax.legend()
    ax.grid(alpha=0.3)
    _guardar(fig, ruta)
    return fig


def _guardar(fig, ruta) -> None:
    """Guarda y cierra la figura si se indicó una ruta."""
    if ruta:
        fig.savefig(ruta, bbox_inches="tight")
        plt.close(fig)
