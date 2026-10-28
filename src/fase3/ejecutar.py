"""
CLI de prueba de las funciones de predicción.

Uso::

    python -m src.fase3.ejecutar
"""

from __future__ import annotations

import pandas as pd

from src.fase3 import predecir_batch, predecir_venta
from src.fase3.config import RUTA_DATOS


def main() -> None:
    print("=" * 60, "\nPredicción de demanda\n", "=" * 60)

    print(f"P0001 para 2022-03-02: {predecir_venta('P0001', '2022-03-02'):.2f} unidades\n")

    print("Lote para 2022-03-02:")
    for r in predecir_batch(["P0001", "P0002", "P0003", "P0004", "P0005"], "2022-03-02"):
        if "error" in r:
            print(f"  {r['producto_id']}: ERROR - {r['error']}")
        else:
            print(f"  {r['producto_id']}: {r['prediccion']:.2f} unidades")

    # Comparación con un valor real conocido
    df = pd.read_csv(RUTA_DATOS, encoding="utf-8-sig", parse_dates=["fecha_venta"])
    fecha, producto = pd.Timestamp("2022-02-28"), "P0001"
    real = df.loc[
        (df["product_id"] == producto) & (df["fecha_venta"] == fecha), "cantidad_vendida"
    ].iloc[0]
    pred = predecir_venta(producto, fecha)
    print(f"\n{producto} {fecha.date()}: predicho {pred:.2f} | real {real:.2f} | error {abs(pred - real):.2f}")


if __name__ == "__main__":
    main()
