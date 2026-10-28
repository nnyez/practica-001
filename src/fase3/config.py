"""
Configuración de predicción y despliegue.
"""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
RUTA_DATOS = RAIZ / "datos" / "ventas_features.csv"
RUTA_MODELO = RAIZ / "modelos" / "fase2" / "lstm_final.keras"
RUTA_ESCALADOR = RAIZ / "modelos" / "fase2" / "escalador.pkl"

VENTANA = 7  # días de historia que ve el modelo
