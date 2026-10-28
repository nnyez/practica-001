"""
Generación del dataset sintético de ventas de una tienda de retail.

Construye dos archivos (por defecto en `datos/`):

* ``inventory.csv``      -> product_id, nombre, categoria, unidad, stock_actual, fecha_expiracion
* ``sales_history.csv``  -> product_id, nombre, fecha_venta, cantidad_vendida, stock_en_momento

El dataset se deriva del dataset público de Kaggle
"Retail Store Inventory Forecasting Dataset"
(https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset),
pero se reconstruye con nombres de productos en español y con patrones
realistas y reconocibles:

* estacionalidad semanal (más ventas viernes, sábado y domingo),
* impulso en feriados nacionales (Ecuador),
* tendencia suave a lo largo del período,
* ruido aleatorio controlado,
* nivel de stock coherente con las ventas (se reabastece cuando baja).

Uso:
    python src/generar_dataset.py --salida datos --semilla 42
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import holidays

# --------------------------------------------------------------------------- #
# Parámetros del dataset
# --------------------------------------------------------------------------- #
SEMILLA_POR_DEFECTO = 42
FECHA_INICIO = "2022-01-01"
N_DIAS = 60                     # ~2 meses  ->  10 productos x 60 días = 600 filas
PAIS_FERIADOS = "EC"            # Ecuador

# Multiplicadores por día de la semana (lunes=0 ... domingo=6).
# Reflejan el patrón de compras típico: más compras al final de la semana.
FACTOR_DIA_SEMANA = np.array([1.00, 0.95, 0.90, 0.98, 1.18, 1.38, 1.22])

# Impulso adicional en feriados nacionales.
FACTOR_FERIADO = 1.35

# Definición de los 10 productos "reales" de la tienda.
# (product_id, nombre, categoria, unidad, stock_inicial, demanda_base, factor_fin_de_semana)
PRODUCTOS = [
    ("P0001", "Arroz blanco",      "Alimentos",       "kg",      684, 120, 1.10),
    ("P0002", "Leche entera",      "Alimentos",       "litro",   665, 135, 1.05),
    ("P0003", "Pan de molde",      "Alimentos",       "unidad",  780, 145, 1.20),
    ("P0004", "Aceite vegetal",    "Alimentos",       "litro",   495,  95, 1.00),
    ("P0005", "Huevos",            "Alimentos",       "docena",  767, 150, 1.25),
    ("P0006", "Detergente en polvo","Limpieza",       "kg",      727,  90, 1.30),
    ("P0007", "Jabón de baño",     "Cuidado personal","unidad",  594, 110, 1.05),
    ("P0008", "Agua embotellada",  "Bebidas",         "litro",   575, 170, 1.35),
    ("P0009", "Galletas",          "Snacks",          "paquete", 575, 160, 1.40),
    ("P0010", "Papel higiénico",   "Hogar",           "paquete", 748, 100, 1.15),
]


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def feriados_ecuador(fechas: pd.DatetimeIndex, pais: str = PAIS_FERIADOS) -> set:
    """Devuelve el conjunto de fechas (date) que son feriado nacional en `pais`."""
    anios = sorted({f.year for f in fechas})
    cal = holidays.country_holidays(pais, years=anios)
    return set(cal.keys())


def _fechas_expiracion(producto: str, semilla: int) -> str:
    """Fecha de expiración determinística y plausible para cada producto."""
    rng = np.random.default_rng(semilla + int(producto[-2:]))
    dias = int(rng.integers(120, 400))  # entre 4 y 13 meses después del inicio
    return (pd.Timestamp(FECHA_INICIO) + pd.Timedelta(days=dias)).strftime("%Y-%m-%d")


# --------------------------------------------------------------------------- #
# Generación
# --------------------------------------------------------------------------- #
def generar_inventario(semilla: int = SEMILLA_POR_DEFECTO) -> pd.DataFrame:
    """Construye el catálogo de productos (`inventory.csv`)."""
    filas = []
    for pid, nombre, categoria, unidad, stock, _demanda, _fds in PRODUCTOS:
        filas.append(
            {
                "product_id": pid,
                "nombre": nombre,
                "categoria": categoria,
                "unidad": unidad,
                "stock_actual": int(stock),
                "fecha_expiracion": _fechas_expiracion(pid, semilla),
            }
        )
    return pd.DataFrame(filas)


def generar_ventas(
    inventario: pd.DataFrame,
    semilla: int = SEMILLA_POR_DEFECTO,
    fecha_inicio: str = FECHA_INICIO,
    n_dias: int = N_DIAS,
    pais: str = PAIS_FERIADOS,
) -> pd.DataFrame:
    """
    Construye el histórico de ventas (`sales_history.csv`) con patrones realistas.

    Modelo por producto y día:
        cantidad = demanda_base * factor_semana * factor_finde * factor_feriado
                   * tendencia * (1 + ruido)
    """
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range(fecha_inicio, periods=n_dias, freq="D")
    feriados = feriados_ecuador(fechas, pais)

    registros = []
    for pid, nombre, _categoria, _unidad, stock_inicial, demanda_base, fds in PRODUCTOS:
        stock = float(stock_inicial)
        punto_reorden = max(250.0, stock_inicial * 0.45)
        for i, fecha in enumerate(fechas):
            # --- demanda esperada ------------------------------------------------
            f_semana = FACTOR_DIA_SEMANA[fecha.weekday()]
            es_finde = fecha.weekday() >= 5
            f_finde = fds if es_finde else 1.0
            f_feriado = FACTOR_FERIADO if fecha.date() in feriados else 1.0
            tendencia = 0.92 + 0.16 * (i / (n_dias - 1))   # leve crecimiento
            esperado = demanda_base * f_semana * f_finde * f_feriado * tendencia
            cantidad = int(max(1, round(rng.normal(esperado, 0.10 * esperado))))

            # --- nivel de stock --------------------------------------------------
            # Se reporta el stock disponible al inicio del día (antes de la venta).
            stock_momento = int(round(stock))
            stock = max(0.0, stock - cantidad)
            if stock < punto_reorden:
                stock = float(rng.integers(700, 800))      # reabastecimiento

            registros.append(
                {
                    "product_id": pid,
                    "nombre": nombre,
                    "fecha_venta": fecha.strftime("%Y-%m-%d"),
                    "cantidad_vendida": cantidad,
                    "stock_en_momento": stock_momento,
                }
            )

    ventas = pd.DataFrame(registros)
    return ventas.sort_values(["fecha_venta", "product_id"]).reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Punto de entrada
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="Genera el dataset sintético de retail.")
    parser.add_argument("--salida", default="datos", help="Carpeta de salida (por defecto: datos)")
    parser.add_argument("--semilla", type=int, default=SEMILLA_POR_DEFECTO, help="Semilla aleatoria")
    args = parser.parse_args()

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    inventario = generar_inventario(args.semilla)
    ventas = generar_ventas(inventario, args.semilla)

    ruta_inv = salida / "inventory.csv"
    ruta_ven = salida / "sales_history.csv"
    inventario.to_csv(ruta_inv, index=False, encoding="utf-8-sig")
    ventas.to_csv(ruta_ven, index=False, encoding="utf-8-sig")

    print(f"[OK] {ruta_inv}  -> {len(inventario)} productos")
    print(f"[OK] {ruta_ven}  -> {len(ventas)} registros "
          f"({ventas['product_id'].nunique()} productos x {ventas['fecha_venta'].nunique()} días)")


if __name__ == "__main__":
    main()
