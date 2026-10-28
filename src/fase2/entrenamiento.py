"""
Entrenamiento y búsqueda de hiperparámetros (finetuning).

Se entrena con validación temporal, ``EarlyStopping`` para evitar sobreajuste
y un grid pequeño sobre los parámetros que más influyen en este dataset.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import pandas as pd
import tensorflow as tf
from keras.callbacks import EarlyStopping

from . import config
from .modelos import construir_modelo


def entrenar_modelo(
    tipo: str = "lstm",
    X_train=None,
    y_train=None,
    X_val=None,
    y_val=None,
    n_pasos: int = config.VENTANA,
    n_variables: int = 15,
    unidades: int = config.UNIDADES,
    batch_size: int = config.BATCH_SIZE,
    epocas: int = config.EPOCAS,
    paciencia: int = config.PACIENCIA,
    dropout: float = 0.0,
    verbose: int = 2,
):
    """Entrena un modelo y devuelve ``(modelo, historial)``."""
    tf.keras.utils.set_random_seed(config.SEMILLA)

    modelo = construir_modelo(
        tipo=tipo, n_pasos=n_pasos, n_variables=n_variables,
        unidades=unidades, dropout=dropout,
    )
    parada = EarlyStopping(
        monitor="val_loss", patience=paciencia, restore_best_weights=True, verbose=0
    )
    historial = modelo.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epocas,
        batch_size=batch_size,
        callbacks=[parada],
        verbose=verbose,
        shuffle=False,
    )
    return modelo, historial


def buscar_hiperparametros(
    X_train, y_train, X_val, y_val, n_pasos: int, n_variables: int
) -> tuple[dict, pd.DataFrame]:
    """Prueba un grid 2x2 (unidades x batch_size) y elige el menor val_loss."""
    combinaciones = list(
        itertools.product(
            [config.UNIDADES // 3, config.UNIDADES],      # unidades
            [config.BATCH_SIZE // 2, config.BATCH_SIZE],   # batch_size
        )
    )

    filas = []
    mejor_loss = float("inf")
    mejores = {}

    for unidades, batch_size in combinaciones:
        modelo, historial = entrenar_modelo(
            tipo="lstm",
            X_train=X_train, y_train=y_train, X_val=X_val, y_val=y_val,
            n_pasos=n_pasos, n_variables=n_variables,
            unidades=unidades, batch_size=batch_size,
            epocas=config.EPOCAS_FINETUNING, paciencia=config.PACIENCIA,
            verbose=0,
        )
        val_loss = float(min(historial.history["val_loss"]))
        filas.append({
            "unidades": unidades,
            "batch_size": batch_size,
            "epocas": len(historial.history["loss"]),
            "val_loss": val_loss,
        })
        print(f"unidades={unidades:>2} batch_size={batch_size:>2} -> val_loss={val_loss:.4f}")

        if val_loss < mejor_loss:
            mejor_loss = val_loss
            mejores = {"unidades": unidades, "batch_size": batch_size}

    tabla = pd.DataFrame(filas).sort_values("val_loss").reset_index(drop=True)
    return mejores, tabla


def guardar_historial(historial, ruta) -> Path:
    """Guarda el historial de entrenamiento (loss por época) en CSV."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(historial.history)
    df.insert(0, "epoca", range(1, len(df) + 1))
    df.to_csv(ruta, index=False)
    return ruta
