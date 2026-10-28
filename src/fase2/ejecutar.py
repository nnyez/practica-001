"""
Pipeline de modelos: entrena, evalúa y guarda los artefactos.

Uso::

    python -m src.fase2.ejecutar
"""

from __future__ import annotations

import pandas as pd

from . import config
from .datos import cargar_ventas, guardar_escalador, preparar_datos
from .entrenamiento import buscar_hiperparametros, entrenar_modelo, guardar_historial
from .evaluacion import (
    baseline_persistencia,
    desescalar,
    graficar_comparacion,
    graficar_curvas,
    graficar_por_producto,
    graficar_predicciones,
    metricas,
    predecir,
)


def main() -> None:
    # 1. Datos
    print("=" * 60, "\nPreparación de datos\n", "=" * 60)
    dp = preparar_datos()
    print(f"Train {dp.X_train.shape} | Val {dp.X_val.shape} | Test {dp.X_test.shape}")
    print(f"Variables: {dp.n_variables} | Corte test: {pd.Timestamp(dp.fecha_corte).date()}\n")

    # 2. Baseline
    y_test_real = desescalar(dp.y_test, dp.escalador, dp.n_variables)
    y_base_real = desescalar(
        baseline_persistencia(dp.X_test), dp.escalador, dp.n_variables
    )
    m_base = metricas(y_test_real, y_base_real)
    print(f"Baseline: RMSE={m_base['RMSE']:.2f} MAE={m_base['MAE']:.2f} MAPE={m_base['MAPE_%']:.2f}%\n")

    # 3. Finetuning
    print("=" * 60, "\nFinetuning del LSTM\n", "=" * 60)
    mejores, tabla_grid = buscar_hiperparametros(
        dp.X_train, dp.y_train, dp.X_val, dp.y_val, dp.ventana, dp.n_variables
    )
    print(tabla_grid.to_string(index=False))
    print("Mejores parámetros:", mejores, "\n")

    # 4. Modelos finales
    print("=" * 60, "\nEntrenamiento de modelos finales\n", "=" * 60)
    resumen = [{"modelo": "Baseline (persistencia)", **m_base}]
    historiales = {}

    for tipo in ["rnn", "lstm", "lstm_apilada"]:
        modelo, historial = entrenar_modelo(
            tipo=tipo,
            X_train=dp.X_train, y_train=dp.y_train,
            X_val=dp.X_val, y_val=dp.y_val,
            n_pasos=dp.ventana, n_variables=dp.n_variables,
            unidades=mejores["unidades"], batch_size=mejores["batch_size"],
        )
        historiales[tipo] = historial
        guardar_historial(historial, config.DIR_RESULTADOS / f"historial_{tipo}.csv")

        y_pred_real = desescalar(predecir(modelo, dp.X_test), dp.escalador, dp.n_variables)
        m = metricas(y_test_real, y_pred_real)
        resumen.append({"modelo": tipo.upper(), **m})
        print(f"{tipo.upper():12s} RMSE={m['RMSE']:.2f} MAE={m['MAE']:.2f} MAPE={m['MAPE_%']:.2f}%")

        if tipo == "lstm":
            modelo.save(config.RUTA_MODELO)
            y_pred_final = y_pred_real

    # 5. Artefactos
    df_resumen = pd.DataFrame(resumen)
    df_resumen.to_csv(config.DIR_RESULTADOS / "metricas.csv", index=False)
    guardar_escalador(dp.escalador, config.RUTA_ESCALADOR)
    print(f"\nMétricas:  {config.DIR_RESULTADOS / 'metricas.csv'}")
    print(f"Modelo:    {config.RUTA_MODELO}")
    print(f"Escalador: {config.RUTA_ESCALADOR}")

    # 6. Figuras
    graficar_curvas(historiales["lstm"], config.DIR_FIGURAS / "01_curvas_entrenamiento.png")

    df_comp = pd.DataFrame({
        "fecha": dp.meta_test["fecha"].reset_index(drop=True),
        "real": y_test_real,
        "pred": y_pred_final,
    })
    df_diario = df_comp.groupby("fecha")[["real", "pred"]].sum().reset_index()
    graficar_predicciones(
        df_diario["fecha"], df_diario["real"], df_diario["pred"],
        config.DIR_FIGURAS / "02_prediccion_vs_real.png",
    )
    graficar_comparacion(df_resumen, config.DIR_FIGURAS / "03_comparacion_modelos.png")

    producto_top = df_comp.assign(producto=dp.meta_test["product_id"].to_numpy()) \
        .groupby("producto")["real"].sum().idxmax()
    df_prod = df_comp.assign(
        producto=dp.meta_test["product_id"].to_numpy()
    ).query("producto == @producto_top").sort_values("fecha")
    df_prod["nombre"] = cargar_ventas().query("product_id == @producto_top")["nombre"].iloc[0]
    graficar_por_producto(df_prod, config.DIR_FIGURAS / "04_prediccion_producto.png")

    print(f"Figuras:  {config.DIR_FIGURAS}")
    print("\nResumen final:")
    print(df_resumen.sort_values("RMSE").to_string(index=False))


if __name__ == "__main__":
    main()
