"""
Ingeniería de características (feature engineering) del dataset de ventas.

Construye el dataset listo para modelado agregando variables temporales y de
rezago, y lo guarda en `datos/ventas_features.csv`.

Variables creadas
-----------------
Temporales básicas:
    anio, mes, dia_del_mes, dia_semana (0=Lunes), nombre_dia,
    semana_iso, semana_del_periodo (1..N)
Indicadores (las relacionadas con fin de semana y feriados):
    es_fin_de_semana (1 si sábado/domingo, 0 en caso contrario),
    es_feriado (1 si feriado nacional de Ecuador, 0 en caso contrario),
    tipo_dia (4 niveles: Entre semana / Fin de semana /
              Feriado / Feriado (fin de semana))
Rezagos y tendencia (por producto):
    ventas_dia_anterior (lag 1), ventas_hace_7_dias (lag 7),
    promedio_movil_7d, variacion_diaria_pct
Atributos del producto (join con inventario):
    categoria, unidad, stock_actual, dias_para_expirar

Uso:
    python src/feature_engineering.py --datos datos --salida datos/ventas_features.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from analisis_exploratorio import (  # noqa: E402
        PAIS_FERIADOS,
        agregar_variables_temporales,
        cargar_datos,
        unir_inventario,
    )
except ModuleNotFoundError:
    from src.analisis_exploratorio import (  # noqa: E402
        PAIS_FERIADOS,
        agregar_variables_temporales,
        cargar_datos,
        unir_inventario,
    )


# --------------------------------------------------------------------------- #
# Variables
# --------------------------------------------------------------------------- #
def marcar_fin_de_semana(df: pd.DataFrame) -> pd.DataFrame:
    """Crea el indicador `es_fin_de_semana` (1 sábado/domingo, 0 resto)."""
    df = df.copy()
    df["es_fin_de_semana"] = (pd.to_datetime(df["fecha_venta"]).dt.weekday >= 5).astype(int)
    return df


def marcar_feriados(df: pd.DataFrame, pais: str = PAIS_FERIADOS) -> pd.DataFrame:
    """Crea el indicador `es_feriado` a partir del calendario de feriados del país."""
    return agregar_variables_temporales(df, pais)


def crear_rezagos(
    df: pd.DataFrame, col: str = "cantidad_vendida", lags: tuple[int, ...] = (1, 7)
) -> pd.DataFrame:
    """Crea rezagos y un promedio móvil de 7 días, respetando el orden por producto."""
    df = df.sort_values(["product_id", "fecha_venta"]).copy()
    for lag in lags:
        df[f"ventas_lag_{lag}"] = df.groupby("product_id")[col].shift(lag)
    df["promedio_movil_7d"] = (
        df.groupby("product_id")[col].transform(lambda s: s.shift(1).rolling(7, min_periods=1).mean())
    )
    df["ventas_dia_anterior"] = df["ventas_lag_1"]
    df["ventas_hace_7_dias"] = df["ventas_lag_7"]
    df["tipo_dia"] = np.select(
        [(df["es_feriado"] == 1) & (df["es_fin_de_semana"] == 1),
         df["es_feriado"] == 1,
         df["es_fin_de_semana"] == 1],
        ["Feriado (fin de semana)", "Feriado", "Fin de semana"],
        default="Entre semana",
    )
    return df


def crear_variables_temporales(df: pd.DataFrame, pais: str = PAIS_FERIADOS) -> pd.DataFrame:
    """Pipeline completo de variables: temporales + fin de semana + feriados + rezagos."""
    df = agregar_variables_temporales(df, pais)
    df = marcar_fin_de_semana(df)
    df = crear_rezagos(df)
    # Días restantes hasta la expiración del producto (a la fecha de la venta).
    if "fecha_expiracion" in df.columns:
        df["dias_para_expirar"] = (
            pd.to_datetime(df["fecha_expiracion"]) - pd.to_datetime(df["fecha_venta"])
        ).dt.days
    columnas = [
        "product_id", "nombre", "categoria", "unidad", "fecha_venta",
        "anio", "mes", "dia_del_mes", "dia_semana", "nombre_dia",
        "semana_iso", "semana_del_periodo", "es_fin_de_semana", "es_feriado", "tipo_dia",
        "ventas_dia_anterior", "ventas_hace_7_dias", "promedio_movil_7d",
        "cantidad_vendida", "stock_en_momento", "stock_actual", "dias_para_expirar",
    ]
    columnas = [c for c in columnas if c in df.columns]
    return df[columnas].reset_index(drop=True)


def guardar_features(df: pd.DataFrame, ruta: str | Path) -> Path:
    """Guarda el dataset con las variables creadas."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


# --------------------------------------------------------------------------- #
# Punto de entrada
# --------------------------------------------------------------------------- #
def main() -> None:
    base = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Crea las variables de ingeniería de características.")
    parser.add_argument("--datos", default=str(base / "datos"), help="Carpeta con los CSV de entrada")
    parser.add_argument("--salida", default=str(base / "datos" / "ventas_features.csv"),
                        help="Ruta del CSV con las variables creadas")
    parser.add_argument("--pais", default=PAIS_FERIADOS, help="País de feriados (ISO-2)")
    args = parser.parse_args()

    ventas, inventario = cargar_datos(args.datos)
    df = unir_inventario(ventas, inventario)
    features = crear_variables_temporales(df, args.pais)
    ruta = guardar_features(features, args.salida)

    print(f"[OK] {ruta} -> {len(features)} filas x {len(features.columns)} columnas")
    print("Variables creadas:", ", ".join(features.columns))


if __name__ == "__main__":
    main()
