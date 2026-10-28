"""Configuración compartida del proyecto.

Centraliza las rutas base para que Fase 1, 2 y 3 usen las mismas.
"""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
FIGURAS = RAIZ / "figuras"
RESULTADOS = RAIZ / "resultados"
MODELOS = RAIZ / "modelos"
NOTEBOOKS = RAIZ / "notebooks"
SCRIPTS = RAIZ / "scripts"

PAIS_FERIADOS = "EC"
NOMBRES_DIA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
