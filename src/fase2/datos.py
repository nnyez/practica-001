"""
Preparación de datos para los modelos.

Convierte el dataset de ventas (`datos/ventas_features.csv`) en secuencias
tridimensionales ``(muestras, ventana, variables)`` listas para una RNN/LSTM.

Reglas importantes:

* La serie se construye **por producto** y en orden cronológico.
* La división train/validación/test es **temporal** (nunca aleatoria).
* El escalador se ajusta **solo con el conjunto de entrenamiento**.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from . import config


@dataclass
class DatosPreparados:
    """Arreglos y metadatos listos para entrenar y evaluar."""

    X_train: np.ndarray
    y_train: np.ndarray
    X_val: np.ndarray
    y_val: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    meta_train: pd.DataFrame
    meta_val: pd.DataFrame
    meta_test: pd.DataFrame
    escalador: MinMaxScaler
    columnas: list[str]
    ventana: int
    fecha_corte: pd.Timestamp | None = None

    @property
    def n_variables(self) -> int:
        """Número de variables por paso de tiempo."""
        return len(self.columnas)


# --------------------------------------------------------------------------- #
# Carga y variables derivadas
# --------------------------------------------------------------------------- #
def cargar_ventas(ruta=config.RUTA_DATOS) -> pd.DataFrame:
    """Carga el dataset de ventas y lo ordena por producto y fecha."""
    df = pd.read_csv(ruta, encoding="utf-8-sig", parse_dates=["fecha_venta"])
    return df.sort_values(["product_id", "fecha_venta"]).reset_index(drop=True)


def agregar_codificacion_ciclica(df: pd.DataFrame) -> pd.DataFrame:
    """Codifica `dia_semana` como seno/coseno para respetar el ciclo semanal."""
    df = df.copy()
    angulo = 2 * np.pi * df["dia_semana"] / 7
    df["dia_sin"] = np.sin(angulo)
    df["dia_cos"] = np.cos(angulo)
    return df


def preparar_tabla(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Añade la codificación cíclica y el one-hot de producto.

    Devuelve el DataFrame y la lista ordenada de columnas que usa el modelo:
    objetivo, variables temporales y una columna por producto.
    """
    df = agregar_codificacion_ciclica(df)
    onehot = pd.get_dummies(df["product_id"], prefix="prod", dtype="float32")
    df = pd.concat([df, onehot], axis=1)

    columnas = [config.COLUMNA_OBJETIVO, *config.COLUMNAS_TEMPORALES, *onehot.columns.tolist()]
    return df, columnas


# --------------------------------------------------------------------------- #
# División temporal y escalado
# --------------------------------------------------------------------------- #
def fechas_de_corte(df: pd.DataFrame, fraccion_prueba: float, fraccion_validacion: float):
    """Devuelve las fechas de corte de test y de validación (temporal)."""
    fechas = np.sort(df["fecha_venta"].unique())
    n_train = int(len(fechas) * (1 - fraccion_prueba))
    fechas_train = fechas[:n_train]
    n_val = int(len(fechas_train) * (1 - fraccion_validacion))
    return fechas[n_train], fechas_train[n_val]


def escalar(df: pd.DataFrame, columnas: list[str], mascara_train: np.ndarray):
    """Ajusta un MinMaxScaler con el train y transforma todo el dataset."""
    escalador = MinMaxScaler(feature_range=(0, 1))
    escalador.fit(df.loc[mascara_train, columnas].to_numpy())
    df = df.copy()
    df[columnas] = escalador.transform(df[columnas].to_numpy()).astype("float32")
    return df, escalador


# --------------------------------------------------------------------------- #
# Secuencias (ventana deslizante)
# --------------------------------------------------------------------------- #
def crear_secuencias(df: pd.DataFrame, columnas: list[str], ventana: int):
    """Convierte la serie de cada producto en ventanas ``(ventana, variables)``."""
    X, y, meta = [], [], []
    for producto, grupo in df.groupby("product_id", sort=True):
        valores = grupo[columnas].to_numpy(dtype="float32")
        fechas = grupo["fecha_venta"].to_numpy()
        for i in range(ventana, len(grupo)):
            X.append(valores[i - ventana:i])
            y.append(valores[i, 0])
            meta.append({"product_id": producto, "fecha": fechas[i]})
    return np.asarray(X, dtype="float32"), np.asarray(y, dtype="float32"), pd.DataFrame(meta)


def _seleccionar(meta: pd.DataFrame, X: np.ndarray, y: np.ndarray, mascara: np.ndarray):
    """Filtra los arreglos según una máscara booleana sobre los metadatos."""
    return X[mascara], y[mascara], meta.loc[mascara].reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Persistencia del escalador
# --------------------------------------------------------------------------- #
def guardar_escalador(escalador, ruta=config.RUTA_ESCALADOR) -> Path:
    """Guarda el MinMaxScaler para reutilizarlo en predicción."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(escalador, ruta)
    return ruta


def cargar_escalador(ruta=config.RUTA_ESCALADOR):
    """Carga el MinMaxScaler guardado durante el entrenamiento."""
    return joblib.load(ruta)


# --------------------------------------------------------------------------- #
# Pipeline completo
# --------------------------------------------------------------------------- #
def preparar_datos(
    ruta=config.RUTA_DATOS,
    ventana: int = config.VENTANA,
    fraccion_prueba: float = config.FRACCION_PRUEBA,
    fraccion_validacion: float = config.FRACCION_VALIDACION,
) -> DatosPreparados:
    """Ejecuta carga, variables, división temporal, escalado y secuencias."""
    df = cargar_ventas(ruta)
    df, columnas = preparar_tabla(df)

    fecha_corte, fecha_val = fechas_de_corte(df, fraccion_prueba, fraccion_validacion)
    mascara_train = (df["fecha_venta"] < fecha_corte).to_numpy()

    df, escalador = escalar(df, columnas, mascara_train)
    X, y, meta = crear_secuencias(df, columnas, ventana)

    en_train = (meta["fecha"] < fecha_corte).to_numpy()
    en_val = en_train & (meta["fecha"] >= fecha_val).to_numpy()

    X_train, y_train, meta_train = _seleccionar(meta, X, y, en_train & ~en_val)
    X_val, y_val, meta_val = _seleccionar(meta, X, y, en_val)
    X_test, y_test, meta_test = _seleccionar(meta, X, y, ~en_train)

    return DatosPreparados(
        X_train=X_train, y_train=y_train,
        X_val=X_val, y_val=y_val,
        X_test=X_test, y_test=y_test,
        meta_train=meta_train, meta_val=meta_val, meta_test=meta_test,
        escalador=escalador, columnas=columnas,
        ventana=ventana, fecha_corte=fecha_corte,
    )
