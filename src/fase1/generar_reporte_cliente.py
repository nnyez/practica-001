"""
Generación del reporte para el cliente (DOCX -> PDF).

Reporte ejecutivo que consolida las 3 fases (datos, modelo, predicción) y
está pensado para convencer al cliente de implementar el modelo. Tono de
negocio, sin tecnicismos innecesarios.

Estructura: análisis de datos primero, luego resultados del modelo, con una
gráfica de predicción que se extiende más allá de los valores reales.

Uso:
    python src/fase1/generar_reporte_cliente.py
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import holidays
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from tensorflow.keras.models import load_model

BASE = Path(__file__).resolve().parent.parent.parent
FIG = BASE / "figuras"
REPORTE = BASE / "reporte"
MODELOS = BASE / "modelos" / "fase2"

URL_KAGGLE = "https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset"


def cargar():
    ventas = pd.read_csv(BASE / "datos" / "sales_history.csv", encoding="utf-8-sig")
    inventario = pd.read_csv(BASE / "datos" / "inventory.csv", encoding="utf-8-sig")
    features = pd.read_csv(BASE / "datos" / "ventas_features.csv", encoding="utf-8-sig")
    ventas["fecha_venta"] = pd.to_datetime(ventas["fecha_venta"])
    inventario["fecha_expiracion"] = pd.to_datetime(inventario["fecha_expiracion"])
    features["fecha_venta"] = pd.to_datetime(features["fecha_venta"])
    return ventas, inventario, features


# --------------------------------------------------------------------------- #
# Generación de la gráfica de forecast (predicciones más allá de los reales)
# --------------------------------------------------------------------------- #
def generar_forecast(n_futuro=14):
    """Genera figuras/forecast_futuro.png: real (histórico) + predicción que
    se extiende más allá de los valores reales."""
    ruta = FIG / "reporte" / "forecast_futuro.png"
    if ruta.exists():
        return ruta

    df = pd.read_csv(BASE / "datos" / "ventas_features.csv", encoding="utf-8-sig",
                     parse_dates=["fecha_venta"])
    productos = sorted(df["product_id"].unique())
    pos = {p: i for i, p in enumerate(productos)}
    feriados = set(holidays.country_holidays("EC", years=[2022]).keys())

    model = load_model(MODELOS / "lstm_final.keras")
    scaler = joblib.load(MODELOS / "escalador.pkl")
    n_vars = 15

    # Real daily totals
    real_daily = df.groupby("fecha_venta")["cantidad_vendida"].sum()

    # Initial window: last 7 real days per product (quantities in original scale)
    windows = {}
    for p in productos:
        hist = df[df["product_id"] == p].sort_values("fecha_venta").tail(7)
        windows[p] = list(hist["cantidad_vendida"].values.astype(float))

    last_date = df["fecha_venta"].max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=n_futuro, freq="D")

    # In-sample predictions for the test period (last 15 days) — from the model
    # We compute them to draw the dashed line overlapping the real series.
    test_dates = sorted(df["fecha_venta"].unique())[-15:]
    # Collect per-product test predictions
    test_preds = {p: {} for p in productos}
    for p in productos:
        hist_p = df[df["product_id"] == p].sort_values("fecha_venta")
        ppos = pos[p]
        for td in test_dates:
            prev = hist_p[hist_p["fecha_venta"] < td].tail(7)
            if len(prev) < 7:
                continue
            X = np.zeros((7, n_vars), dtype="float32")
            for i in range(7):
                row = prev.iloc[i]
                d = row["fecha_venta"]
                X[i, 0] = row["cantidad_vendida"]
                X[i, 1] = 1 if d.weekday() >= 5 else 0
                X[i, 2] = 1 if d.date() in feriados else 0
                ang = 2 * np.pi * d.weekday() / 7
                X[i, 3] = np.sin(ang)
                X[i, 4] = np.cos(ang)
                X[i, 5 + ppos] = 1.0
            Xs = scaler.transform(X).reshape(1, 7, n_vars)
            pred_s = model.predict(Xs, verbose=0)[0, 0]
            dummy = np.zeros((1, n_vars), dtype="float32")
            dummy[0, 0] = pred_s
            pred = scaler.inverse_transform(dummy)[0, 0]
            test_preds[p][td] = max(0.0, float(pred))

    # Out-of-sample (future) predictions
    future_preds = {p: [] for p in productos}
    for fdate in future_dates:
        for p in productos:
            w = windows[p]
            ppos = pos[p]
            X = np.zeros((7, n_vars), dtype="float32")
            for i in range(7):
                # quantity: from the sliding window (last 7)
                X[i, 0] = w[i]
                day_date = fdate - pd.Timedelta(days=7 - i)
                X[i, 1] = 1 if day_date.weekday() >= 5 else 0
                X[i, 2] = 1 if day_date.date() in feriados else 0
                ang = 2 * np.pi * day_date.weekday() / 7
                X[i, 3] = np.sin(ang)
                X[i, 4] = np.cos(ang)
                X[i, 5 + ppos] = 1.0
            Xs = scaler.transform(X).reshape(1, 7, n_vars)
            pred_s = model.predict(Xs, verbose=0)[0, 0]
            dummy = np.zeros((1, n_vars), dtype="float32")
            dummy[0, 0] = pred_s
            pred = scaler.inverse_transform(dummy)[0, 0]
            pred = max(0.0, float(pred))
            future_preds[p].append(pred)
            # slide window
            w.append(pred)
            w.pop(0)

    # Aggregate per day
    # In-sample: test period
    test_pred_daily = {}
    for td in test_dates:
        test_pred_daily[td] = sum(test_preds[p].get(td, 0) for p in productos)
    # Future
    future_pred_daily = [sum(future_preds[p][d] for p in productos) for d in range(len(future_dates))]

    # Plot
    fig, ax = plt.subplots(figsize=(12, 5.5))
    all_dates = list(real_daily.index)
    ax.plot(all_dates, real_daily.values, color="#1f3864", linewidth=2,
            marker="o", ms=3, label="Ventas reales (histórico)")

    # Forecast line: test period (dashed) + future (dashed, extended)
    forecast_dates = list(test_dates) + list(future_dates)
    forecast_vals = [test_pred_daily[td] for td in test_dates] + future_pred_daily
    ax.plot(forecast_dates, forecast_vals, color="#e63946", linewidth=2,
            linestyle="--", marker="s", ms=4, label="Predicción del modelo")

    # Vertical line at "hoy"
    ax.axvline(x=last_date, color="gray", linestyle=":", linewidth=1.5, label="Hoy (último dato real)")
    ax.text(last_date, ax.get_ylim()[1] * 0.95, "  hoy", color="gray", fontsize=10)

    ax.set_title("Ventas diarias: histórico real vs predicción (extendida al futuro)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Ventas totales (unidades/día)")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(ruta, bbox_inches="tight", dpi=130)
    plt.close(fig)
    print(f"[figura] {ruta}")
    return ruta


# --------------------------------------------------------------------------- #
# Helpers DOCX
# --------------------------------------------------------------------------- #
def _titulo(doc, texto, nivel=1):
    doc.add_heading(texto, level=nivel)


def _parrafo(doc, texto, negrita=False, cursiva=False, tamano=None):
    p = doc.add_paragraph()
    r = p.add_run(texto)
    r.bold = negrita
    r.italic = cursiva
    if tamano:
        r.font.size = Pt(tamano)
    return p


def _vineta(doc, texto):
    doc.add_paragraph(texto, style="List Bullet")


def _figura(doc, nombre, ancho=5.5):
    ruta = FIG / nombre
    if ruta.exists():
        doc.add_picture(str(ruta), width=Inches(ancho))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        _parrafo(doc, f"[Falta la figura {nombre}]")


def _tabla(doc, df, titulo=None, tamano=9):
    if titulo:
        _parrafo(doc, titulo, negrita=True)
    tabla = doc.add_table(rows=1, cols=len(df.columns))
    tabla.style = "Light Grid Accent 1"
    for j, col in enumerate(df.columns):
        tabla.rows[0].cells[j].text = str(col)
        for r in tabla.rows[0].cells[j].paragraphs[0].runs:
            r.bold = True
            r.font.size = Pt(tamano)
    for _, fila in df.iterrows():
        celdas = tabla.add_row().cells
        for j, col in enumerate(df.columns):
            celdas[j].text = "" if pd.isna(fila[col]) else str(fila[col])
            for r in celdas[j].paragraphs[0].runs:
                r.font.size = Pt(tamano)
    return tabla


# --------------------------------------------------------------------------- #
# Construcción
# --------------------------------------------------------------------------- #
def construir(ventas, inventario, features) -> Path:
    REPORTE.mkdir(parents=True, exist_ok=True)
    doc = Document()
    est = doc.styles["Normal"].font
    est.name = "Calibri"
    est.size = Pt(11)

    # --- Portada ---
    t = doc.add_heading("Predicción de demanda para reducir quiebres de stock", level=0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("Reporte para el cliente · Solución de predicción de demanda diaria")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True
    doc.add_paragraph("Preparado a partir del análisis de ventas de una tienda de barrio (10 productos, 60 días).")
    doc.add_paragraph()

    # --- 1. Resumen ejecutivo ---
    _titulo(doc, "1. Resumen ejecutivo")
    _parrafo(doc, "Hoy la tienda repone 'a ojo': quiebres de stock en fin de semana y sobrestock entre semana. "
                  "La demanda tiene un patrón claro que se puede predecir con un error del 10.9 %.")
    _vineta(doc, "El fin de semana vende un 55.6 % más que entre semana; los feriados, un 40.1 % más.")
    _vineta(doc, "El modelo reduce el error de pronóstico de 19.5 % a 10.9 % (un 45 % menos).")
    _vineta(doc, "Eso equivale a unas 130 unidades menos de error al día en la tienda (10 productos).")
    _vineta(doc, "El pipeline ya está listo: solo falta calibrarlo con los datos reales del negocio.")
    _parrafo(doc, "Pedido al cliente: aprobar un piloto de 4 a 6 semanas con datos reales y compartir el histórico de ventas.",
             negrita=True)

    # --- 2. El problema del negocio ---
    _titulo(doc, "2. El problema del negocio")
    _parrafo(doc, "En una tienda de barrio la reposición se hace por intuición. Cuando la demanda sube (fin de semana, "
                  "feriados) hay quiebre de stock y se pierden ventas; cuando baja, hay capital inmovilizado en inventario. "
                  "La pregunta que el modelo responde es simple: ¿cuánto venderé mañana de cada producto?")
    _vineta(doc, "Quiebres de stock en los días de mayor flujo (fines de semana y feriados).")
    _vineta(doc, "Sobrestock en los días de menor flujo (miércoles, días normales).")
    _vineta(doc, "Sin una previsión, el pedido se dimensiona por promedio, que falla todos los fines de semana.")

    # --- 3. La solución ---
    _titulo(doc, "3. La solución")
    _parrafo(doc, "Construimos un modelo que estima la demanda diaria por producto usando el historial de ventas y el "
                  "calendario. El modelo mira los últimos 7 días de cada producto y el calendario, y estima la venta del "
                  "día siguiente.")
    _vineta(doc, "Un solo modelo aprende los 10 productos (identifica cuál por su código).")
    _vineta(doc, "Usa las variables que importan en este negocio: fin de semana, feriados y memoria de ventas recientes.")
    _vineta(doc, "Se entrega listo para integrar: recibe un producto (o un lote) y una fecha, y devuelve la predicción.")
    _figura(doc, "reporte/ventana_7dias.png", ancho=5.5)

    # --- 4. Los datos ---
    _titulo(doc, "4. Los datos")
    _parrafo(doc, "El dataset de partida es público, de Kaggle: Retail Store Inventory Forecasting Dataset.")
    _vineta(doc, f"URL de origen: {URL_KAGGLE}")
    _vineta(doc, "Tipo: el dataset base es público; el dataset analizado fue construido a partir de él.")
    _vineta(doc, "Dataset construido: 10 productos reales × 60 días (1 ene – 1 mar 2022) = 600 registros.")
    _parrafo(doc, "Modificaciones realizadas al dataset original:", negrita=True)
    df_mod = pd.DataFrame(
        [
            ["Idioma y nombres", "Columnas en inglés genérico", "Traducido al español; 10 productos reales con categoría y unidad."],
            ["Selección de productos", "20 product_id sin categoría consistente", "10 productos, cada uno con categoría y unidad correctas."],
            ["Período", "731 días (2022–2024)", "60 días (1 ene – 1 mar 2022) para el análisis semana a semana."],
            ["Patrón de compras", "Datos aleatorios (Holiday/Promotion no influye: 136.5 vs 136.4)", "Estacionalidad semanal, impulso en feriados de Ecuador y tendencia leve."],
            ["Estructura de archivos", "Un único archivo ancho", "Separado en catálogo (inventory.csv) e historial de ventas (sales_history.csv)."],
        ],
        columns=["Aspecto", "Dataset original", "Dataset construido"],
    )
    _tabla(doc, df_mod, tamano=8)
    _parrafo(doc, "Categorías y productos analizados:", negrita=True)
    df_cat = pd.DataFrame(
        [
            ["Alimentos", 45011, "49.6 %", 150.0, "Arroz, Leche, Pan, Aceite, Huevos"],
            ["Bebidas", 12731, "14.0 %", 212.2, "Agua embotellada"],
            ["Snacks", 11968, "13.2 %", 199.5, "Galletas"],
            ["Cuidado personal", 7417, "8.2 %", 123.6, "Jabón de baño"],
            ["Hogar", 7014, "7.7 %", 116.9, "Papel higiénico"],
            ["Limpieza", 6593, "7.3 %", 109.9, "Detergente en polvo"],
        ],
        columns=["Categoría", "Ventas totales", "Participación", "Prom. diario", "Productos"],
    )
    _tabla(doc, df_cat, tamano=8)
    _figura(doc, "fase1/01_ventas_por_categoria.png", ancho=5.5)
    _figura(doc, "fase1/11_tres_categorias_por_semana.png", ancho=5.5)

    # --- 5. Lo que encontramos ---
    _titulo(doc, "5. Lo que encontramos en los datos")
    _parrafo(doc, "El comportamiento de las compras muestra un patrón semanal claro y recurrente.")
    _vineta(doc, "Sábado: 2.183 unidades/día (pico). Miércoles: 1.117 unidades/día (valle).")
    _vineta(doc, "Fin de semana vende un 55.6 % más que entre semana (2.016,7 vs 1.296,0).")
    _vineta(doc, "Feriados venden un 40.1 % más (2.077,3 vs 1.482,5). Feriados usados: 1 ene, 28 feb y 1 mar (Ecuador).")
    _vineta(doc, "1 de enero (sábado + Año Nuevo) fue el pico más alto del período: 2.753 unidades.")
    _vineta(doc, "Alimentos concentra el 49.6 % de las ventas, pero Bebidas y Snacks son los más rotativos por producto (212 y 199 unidades/día).")
    _figura(doc, "fase1/07_fin_de_semana.png", ancho=5.5)
    _figura(doc, "fase1/08_feriados.png", ancho=5.5)

    # --- 6. Las variables que creamos ---
    _titulo(doc, "6. Las variables que creamos")
    _parrafo(doc, "A partir de la fecha y del negocio creamos variables que el modelo necesita:")
    df_vars = pd.DataFrame(
        [
            ["es_fin_de_semana", "1 si es sábado o domingo. Efecto confirmado: +55.6 %."],
            ["es_feriado", "1 si es feriado nacional de Ecuador. Efecto confirmado: +40.1 %."],
            ["tipo_dia", "Clasificación en 4 niveles (sin pérdida de información)."],
            ["dia_semana / mes", "Componentes de la fecha para capturar el ciclo semanal y mensual."],
            ["semana_del_periodo", "Semana dentro del período (1..9) para el análisis semana a semana."],
            ["ventas_dia_anterior", "Ventas del día anterior por producto (memoria inmediata)."],
            ["ventas_hace_7_dias", "Ventas del mismo día de la semana anterior (estacionalidad)."],
            ["promedio_movil_7d", "Promedio de los 7 días previos por producto (tendencia local)."],
            ["dias_para_expirar", "Días entre la venta y la expiración del producto."],
        ],
        columns=["Variable", "Para qué sirve (negocio)"],
    )
    _tabla(doc, df_vars, tamano=9)
    _parrafo(doc, "La justificación de cada variable viene del negocio: en una tienda de barrio el flujo se concentra "
                  "en fin de semana y feriados, por eso esos indicadores son obligatorios. Los rezagos dan memoria al "
                  "modelo para que aprenda de la historia reciente.", cursiva=True)

    # --- 7. Resultados del modelo ---
    _titulo(doc, "7. Resultados del modelo")
    _parrafo(doc, "El modelo predice la demanda diaria por producto con un error del 10.9 %, frente al 19.5 % del "
                  "método actual (repetir la venta de ayer).")
    df_res = pd.DataFrame(
        [
            ["Método actual (repetir venta de ayer)", 44.12, 32.43, 19.54],
            ["Modelo predictivo", 24.28, 17.97, 10.88],
        ],
        columns=["Método", "Error RMSE", "Error MAE", "Error MAPE (%)"],
    )
    _tabla(doc, df_res, tamano=10)
    _parrafo(doc, "El modelo reduce el error un 45 %.", negrita=True)
    _vineta(doc, "División temporal: 75 % train / 25 % test (últimos 15 días). Nunca aleatoria.")
    _vineta(doc, "El escalado se ajusta solo con train: sin fuga de información.")
    _vineta(doc, "El baseline de persistencia es la referencia obligatoria del forecasting.")
    _vineta(doc, "Test: 150 predicciones (15 días × 10 productos).")
    _figura(doc, "fase2/02_prediccion_vs_real.png", ancho=5.5)
    _figura(doc, "reporte/forecast_futuro.png", ancho=5.5)
    _parrafo(doc, "La gráfica muestra las ventas reales (línea sólida) y las predicciones del modelo (línea "
                  "discontinua). Las predicciones se extienden más allá de los valores reales, mostrando la "
                  "proyección del modelo para los próximos días.", cursiva=True, tamano=9)

    # --- 8. Impacto para el negocio ---
    _titulo(doc, "8. Impacto para el negocio")
    _parrafo(doc, "Traducir el error a unidades permite dimensionar el pedido con más precisión.")
    _vineta(doc, "Venta media por producto y día: 151 unidades.")
    _vineta(doc, "Error por producto y día: 16 unidades (modelo) vs 29 (método actual).")
    _vineta(doc, "En la tienda completa: unas 130 unidades diarias menos de error en el pedido.")
    _vineta(doc, "Beneficio esperado: menos quiebres de stock en fin de semana y feriados, y menos capital inmovilizado entre semana.")
    _figura(doc, "reporte/impacto_unidades.png", ancho=5.5)
    _parrafo(doc, "Nota: la traducción a dinero es ilustrativa (supuesto de precio promedio por unidad). "
                  "Se valida con los precios reales del cliente.", cursiva=True, tamano=9)

    # --- 9. Anexo: transparencia ---
    _titulo(doc, "9. Anexo: transparencia y metodología")
    _parrafo(doc, "Cómo se construyó (en lenguaje simple):", negrita=True)
    _vineta(doc, "Se partió de un dataset público (Kaggle) y se construyó uno propio de 10 productos × 60 días.")
    _vineta(doc, "Se verificó la calidad: sin nulos, sin duplicados, sin valores negativos, 60 días de cobertura.")
    _vineta(doc, "Se crearon variables de calendario (fin de semana, feriados) y memoria (ventas de días anteriores).")
    _vineta(doc, "Se entrenó un modelo de red neuronal recurrente que mira los últimos 7 días y estima la venta del día siguiente.")
    _vineta(doc, "Se comparó contra el método actual (repetir la venta de ayer): el modelo reduce el error un 45 %.")
    _parrafo(doc, "Limitaciones (para tomar decisiones con criterio):", negrita=True)
    _vineta(doc, "Dataset sintético de 60 días; solo 150 predicciones de test.")
    _vineta(doc, "Solo 3 días feriado en la ventana: la estimación del efecto feriado es preliminar.")
    _vineta(doc, "El modelo necesita los 7 días previos reales para predecir.")
    _vineta(doc, "Sin datos reales, el error real del negocio puede diferir.")
    _parrafo(doc, "Métricas usadas: RMSE (penaliza errores grandes), MAE (error medio en unidades), "
                  "MAPE (error porcentual, permite comparar entre productos).", tamano=9, cursiva=True)

    ruta = REPORTE / "reporte_cliente.docx"
    doc.save(ruta)
    print(f"[OK] {ruta}")
    return ruta


def convertir_pdf(ruta: Path) -> None:
    if shutil.which("libreoffice") is None:
        print("[aviso] LibreOffice no disponible; se omite la conversión a PDF.")
        return
    perfil = BASE / ".libreoffice_profile"
    subprocess.run(
        ["libreoffice", "--headless", f"-env:UserInstallation=file://{perfil}",
         "--convert-to", "pdf", "--outdir", str(ruta.parent), str(ruta)],
        check=False, capture_output=True, timeout=300,
    )
    pdf = ruta.with_suffix(".pdf")
    print(f"[{'OK' if pdf.exists() else 'aviso'}] {pdf}")


def main() -> None:
    ventas, inventario, features = cargar()
    generar_forecast(14)
    docx = construir(ventas, inventario, features)
    convertir_pdf(docx)


if __name__ == "__main__":
    main()
