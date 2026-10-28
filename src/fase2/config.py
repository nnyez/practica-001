"""
Configuración de la Fase 2: desarrollo y entrenamiento de modelos.

Concentra rutas, hiperparámetros y columnas usadas por todos los módulos del
paquete para evitar valores "mágicos" repartidos por el código.
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Rutas del proyecto
# --------------------------------------------------------------------------- #
RAIZ = Path(__file__).resolve().parent.parent.parent
RUTA_DATOS = RAIZ / "datos" / "ventas_features.csv"
DIR_RESULTADOS = RAIZ / "resultados" / "fase2"
DIR_FIGURAS = RAIZ / "figuras" / "fase2"
DIR_MODELOS = RAIZ / "modelos" / "fase2"

# Artefactos reutilizables en predicción
RUTA_MODELO = DIR_MODELOS / "lstm_final.keras"
RUTA_ESCALADOR = DIR_MODELOS / "escalador.pkl"

# --------------------------------------------------------------------------- #
# Variables del problema
# --------------------------------------------------------------------------- #
COLUMNA_OBJETIVO = "cantidad_vendida"

# Variables de calendario que acompañan a la serie de ventas en cada paso de
# tiempo. `dia_sin`/`dia_cos` codifican el día de la semana de forma cíclica.
COLUMNAS_TEMPORALES = ["es_fin_de_semana", "es_feriado", "dia_sin", "dia_cos"]

# --------------------------------------------------------------------------- #
# Hiperparámetros por defecto
# --------------------------------------------------------------------------- #
VENTANA = 7          # días de historia que ve el modelo para predecir el día t
SEMILLA = 42
FRACCION_PRUEBA = 0.25       # 25 % final del período = test
FRACCION_VALIDACION = 0.20   # 20 % final del train = validación

EPOCAS = 120
EPOCAS_FINETUNING = 80
PACIENCIA = 12
BATCH_SIZE = 32
UNIDADES = 50
