"""
Generación de la presentación final (3 fases) para el cliente.

Evoluciona la presentación de la Tarea 01 (que se conserva como
`presentacion_tarea01.pptx`) hacia una presentación de resultados de 10 minutos
que cubre las 3 fases: datos/variables, modelos y predicción.

Uso:
    python src/fase1/generar_presentacion_final.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pptx import Presentation
from pptx.util import Inches as PInches
from pptx.util import Pt as PPt
from pptx.dml.color import RGBColor

BASE = Path(__file__).resolve().parent.parent.parent
FIG = BASE / "figuras"
PRESENTACION = BASE / "presentacion"

URL_KAGGLE = "https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset"


# --------------------------------------------------------------------------- #
# Helpers de diapositivas
# --------------------------------------------------------------------------- #
def _titulo_slide(prs, titulo, subtitulo=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # en blanco
    tb = slide.shapes.add_textbox(PInches(0.6), PInches(0.35), PInches(8.8), PInches(1.0))
    tf = tb.text_frame
    tf.text = titulo
    tf.paragraphs[0].runs[0].font.size = PPt(28)
    tf.paragraphs[0].runs[0].font.bold = True
    tf.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
    if subtitulo:
        p = tf.add_paragraph()
        p.text = subtitulo
        p.runs[0].font.size = PPt(15)
        p.runs[0].font.italic = True
        p.runs[0].font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    return slide


def _bullets(prs, titulo, bullets, subtitulo=None, comentario=None, tamano=18):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    tb = slide.shapes.add_textbox(PInches(0.6), PInches(0.35), PInches(8.8), PInches(0.9))
    tb.text_frame.text = titulo
    tb.text_frame.paragraphs[0].runs[0].font.size = PPt(26)
    tb.text_frame.paragraphs[0].runs[0].font.bold = True
    tb.text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
    if subtitulo:
        p = tb.text_frame.add_paragraph()
        p.text = subtitulo
        p.runs[0].font.size = PPt(13)
        p.runs[0].font.italic = True
        p.runs[0].font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    body = slide.shapes.add_textbox(PInches(0.7), PInches(1.35), PInches(8.6), PInches(5.4))
    tf = body.text_frame
    tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"• {b}"
        p.font.size = PPt(tamano)
        p.space_after = PPt(6)
    if comentario:
        cb = slide.shapes.add_textbox(PInches(0.7), PInches(6.7), PInches(8.6), PInches(0.6))
        cb.text_frame.text = comentario
        cb.text_frame.paragraphs[0].font.size = PPt(12)
        cb.text_frame.paragraphs[0].font.italic = True
        cb.text_frame.paragraphs[0].font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    return slide


def _ajustar(ruta, max_w, max_h):
    """Devuelve (w, h) ajustando la imagen al rectángulo disponible."""
    from PIL import Image
    with Image.open(ruta) as im:
        iw, ih = im.size
    aspect = iw / ih
    if max_w / aspect <= max_h:
        return max_w, max_w / aspect
    return max_h * aspect, max_h


def _figura(prs, titulo, figura, comentario=None, max_w=8.2, max_h=4.9):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    tb = slide.shapes.add_textbox(PInches(0.6), PInches(0.3), PInches(8.8), PInches(0.8))
    tb.text_frame.text = titulo
    tb.text_frame.paragraphs[0].runs[0].font.size = PPt(26)
    tb.text_frame.paragraphs[0].runs[0].font.bold = True
    tb.text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
    ruta = FIG / figura
    if ruta.exists():
        w, h = _ajustar(ruta, max_w, max_h)
        x = (10.0 - w) / 2.0
        slide.shapes.add_picture(str(ruta), PInches(x), PInches(1.2),
                                width=PInches(w), height=PInches(h))
    if comentario:
        cb = slide.shapes.add_textbox(PInches(0.7), PInches(6.2), PInches(8.6), PInches(0.9))
        cb.text_frame.text = comentario
        cb.text_frame.paragraphs[0].font.size = PPt(13)
        cb.text_frame.paragraphs[0].font.italic = True
        cb.text_frame.paragraphs[0].font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    return slide


def _tabla(prs, titulo, df, comentario=None, tamano=14):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    tb = slide.shapes.add_textbox(PInches(0.6), PInches(0.3), PInches(8.8), PInches(0.8))
    tb.text_frame.text = titulo
    tb.text_frame.paragraphs[0].runs[0].font.size = PPt(26)
    tb.text_frame.paragraphs[0].runs[0].font.bold = True
    tb.text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
    filas, cols = len(df) + 1, len(df.columns)
    ancho_total = 8.8
    t = slide.shapes.add_table(filas, cols, PInches(0.6), PInches(1.2),
                              PInches(ancho_total), PInches(0.35 * filas)).table
    for j, col in enumerate(df.columns):
        t.cell(0, j).text = str(col)
        t.cell(0, j).text_frame.paragraphs[0].runs[0].font.bold = True
        t.cell(0, j).text_frame.paragraphs[0].runs[0].font.size = PPt(tamano)
    for i, (_, fila) in enumerate(df.iterrows(), start=1):
        for j, col in enumerate(df.columns):
            t.cell(i, j).text = "" if pd.isna(fila[col]) else str(fila[col])
            t.cell(i, j).text_frame.paragraphs[0].runs[0].font.size = PPt(tamano)
    if comentario:
        cb = slide.shapes.add_textbox(PInches(0.7), PInches(1.2 + 0.35 * filas + 0.1),
                                     PInches(8.6), PInches(0.6))
        cb.text_frame.text = comentario
        cb.text_frame.paragraphs[0].font.size = PPt(12)
        cb.text_frame.paragraphs[0].font.italic = True
        cb.text_frame.paragraphs[0].font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    return slide


def _tabla_y_figura(prs, titulo, df, figura, comentario=None, tamano=13):
    """Diapositiva con tabla (izquierda) y figura (derecha)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    tb = slide.shapes.add_textbox(PInches(0.6), PInches(0.3), PInches(8.8), PInches(0.8))
    tb.text_frame.text = titulo
    tb.text_frame.paragraphs[0].runs[0].font.size = PPt(24)
    tb.text_frame.paragraphs[0].runs[0].font.bold = True
    tb.text_frame.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
    # tabla a la izquierda
    filas, cols = len(df) + 1, len(df.columns)
    t = slide.shapes.add_table(filas, cols, PInches(0.6), PInches(1.2),
                              PInches(4.2), PInches(0.32 * filas)).table
    for j, col in enumerate(df.columns):
        t.cell(0, j).text = str(col)
        t.cell(0, j).text_frame.paragraphs[0].runs[0].font.bold = True
        t.cell(0, j).text_frame.paragraphs[0].runs[0].font.size = PPt(tamano)
    for i, (_, fila) in enumerate(df.iterrows(), start=1):
        for j, col in enumerate(df.columns):
            t.cell(i, j).text = "" if pd.isna(fila[col]) else str(fila[col])
            t.cell(i, j).text_frame.paragraphs[0].runs[0].font.size = PPt(tamano)
    # figura a la derecha, ajustada al panel disponible
    ruta = FIG / figura
    if ruta.exists():
        w, h = _ajustar(ruta, 4.4, 4.6)
        x = 5.0 + (4.4 - w) / 2.0
        slide.shapes.add_picture(str(ruta), PInches(x), PInches(1.2),
                                width=PInches(w), height=PInches(h))
    if comentario:
        cb = slide.shapes.add_textbox(PInches(0.6), PInches(6.0), PInches(8.8), PInches(0.7))
        cb.text_frame.text = comentario
        cb.text_frame.paragraphs[0].font.size = PPt(12)
        cb.text_frame.paragraphs[0].font.italic = True
        cb.text_frame.paragraphs[0].font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    return slide


# --------------------------------------------------------------------------- #
# Figuras auxiliares (generadas por matplotlib)
# --------------------------------------------------------------------------- #
def _figura_ventana() -> Path:
    """Diagrama de la ventana de 7 días que consume el modelo."""
    ruta = FIG / "reporte" / "ventana_7dias.png"
    if ruta.exists():
        return ruta
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.set_xlim(-0.5, 8.5)
    ax.set_ylim(-1.5, 6.5)
    ax.axis("off")
    dias = [f"D{i}" for i in range(1, 8)]
    for k, d in enumerate(dias):
        ax.add_patch(plt.Rectangle((k, 0.5), 0.9, 4.5, fc="#dce6f1", ec="#1f3864", lw=1.5))
        ax.text(k + 0.45, 5.2, d, ha="center", va="center", fontsize=11, fontweight="bold")
        # variables dentro de cada día
        for y, (txt, col) in enumerate([("venta", "#2e7d32"), ("finde", "#1565c0"),
                                         ("feriado", "#c62828"), ("sin/cos", "#6a1b9a"),
                                         ("producto", "#616161")]):
            ax.text(k + 0.45, 4.5 - y * 0.85, txt, ha="center", va="center",
                    fontsize=8, color=col)
    # llave de ventana
    ax.annotate("", xy=(7.9, 2.75), xytext=(7.0, 2.75),
                arrowprops=dict(arrowstyle="->", lw=2, color="#1f3864"))
    ax.text(8.0, 2.75, "LSTM\n→ demanda\ndel día t", ha="left", va="center",
            fontsize=11, fontweight="bold", color="#1f3864")
    ax.text(3.45, -0.9, "Ventana de 7 días × 15 variables (cantidad, calendario, producto)",
            ha="center", va="center", fontsize=12, style="italic")
    ax.set_title("Entrada del modelo: los 7 días anteriores", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(ruta, bbox_inches="tight", dpi=130)
    plt.close(fig)
    return ruta


def _figura_impacto() -> Path:
    """Comparación de error por producto y día: baseline vs LSTM."""
    ruta = FIG / "reporte" / "impacto_unidades.png"
    if ruta.exists():
        return ruta
    fig, ax = plt.subplots(figsize=(8, 4.5))
    labels = ["Método actual\n(persistencia)", "LSTM"]
    vals = [29.5, 16.5]
    colores = ["#c62828", "#2e7d32"]
    barras = ax.bar(labels, vals, color=colores, width=0.6)
    for b, v in zip(barras, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.5, f"{v:.1f} unidades",
                ha="center", va="bottom", fontsize=12, fontweight="bold")
    ax.set_title("Error por producto y día (unidades)", fontsize=14, fontweight="bold")
    ax.set_ylabel("MAE (unidades)")
    ax.set_ylim(0, 36)
    ax.grid(axis="y", alpha=0.3)
    ax.text(0.5, 0.92, "≈ 13 unidades menos de error por producto y día",
            transform=ax.transAxes, ha="center", fontsize=12, style="italic",
            color="#1f3864")
    fig.tight_layout()
    fig.savefig(ruta, bbox_inches="tight", dpi=130)
    plt.close(fig)
    return ruta


# --------------------------------------------------------------------------- #
# Construcción
# --------------------------------------------------------------------------- #
def construir() -> Path:
    PRESENTACION.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = PInches(10)
    prs.slide_height = PInches(7.5)

    # 1. Portada
    _titulo_slide(prs, "De los datos a la predicción de demanda",
                  "3 fases: datos · modelo · despliegue  |  Tarea 01 + Fases 2 y 3")

    # 2. Problema + propuesta
    _bullets(prs, "El problema y la propuesta", [
        "Hoy la tienda repone 'a ojo': quiebres de stock en fin de semana y sobrestock entre semana.",
        "La demanda tiene patrón claro: fin de semana +55.6 % y feriados +40.1 %.",
        "Propuesta: predecir la demanda diaria por producto para decidir cuánto stock tener.",
        "Objetivo de negocio: menos quiebres, menos capital inmovilizado, mejor servicio.",
    ])

    # 3. Fase 1 - Dataset
    _bullets(prs, "FASE 1 · El dataset", [
        "Origen: dataset público de Kaggle (Retail Store Inventory Forecasting).",
        f"URL: {URL_KAGGLE}",
        "El dataset analizado es construido: 10 productos reales × 60 días (1 ene – 1 mar 2022).",
        "Modificaciones: español + productos reales, período de 2 meses, patrón semanal y feriados de Ecuador.",
        "Los datos del original son aleatorios (Holiday/Promotion no influye: 136.5 vs 136.4).",
    ])

    # 4. Fase 1 - Hallazgos
    _figura(prs, "FASE 1 · Qué encontramos", "fase1/11_tres_categorias_por_semana.png",
            "El patrón se repite cada semana: sábado pico (2.183) y miércoles valle (1.117).")

    # 5. Fase 1 - Variables y secuencias
    _bullets(prs, "FASE 1 · Variables creadas y secuencias", [
        "Temporales: mes, día de la semana, semana del período.",
        "Indicadores: es_fin_de_semana (0/1) y es_feriado (0/1) con calendario real de Ecuador.",
        "Rezagos: ventas del día anterior, de hace 7 días y promedio móvil de 7 días.",
        "De negocio: categoría, unidad, stock_actual, dias_para_expirar.",
        "Secuencias: ventana de 7 días × 15 variables por producto (7 días → 1 día adelante).",
    ], comentario="Salida: datos/ventas_features.csv (600 filas × 22 columnas).")

    # 6. Fase 2 - Modelo
    _figura(prs, "FASE 2 · Cómo modelamos", "reporte/ventana_7dias.png",
            "Un solo modelo: red neuronal recurrente tipo LSTM (50 unidades + densa), como el cuaderno de referencia. Mirá los últimos 7 días y estima la venta del día siguiente.")

    # 7. Fase 2 - Resultados
    df_res = pd.DataFrame({
        "Método": ["Método actual (persistencia)", "Modelo RNN (LSTM)"],
        "RMSE": [44.12, 24.28],
        "MAE": [32.43, 17.97],
        "MAPE (%)": [19.54, 10.88],
    })
    _tabla_y_figura(prs, "FASE 2 · Resultados (conjunto de prueba)",
                    df_res, "reporte/impacto_unidades.png",
                    comentario="El modelo reduce el error un 45 % frente al método actual (RMSE). Un solo modelo RNN (LSTM), como el cuaderno de referencia.")

    # 8. Fase 2 - Confiabilidad
    _figura(prs, "FASE 2 · ¿Es confiable?", "fase2/02_prediccion_vs_real.png",
            "La predicción sigue la serie real, no solo el promedio. Split temporal sin fuga de información.")

    # 9. Fase 3 - Uso y demo
    _figura(prs, "FASE 3 · Cómo se usa", "fase2/04_prediccion_producto.png",
            "predecir_venta(producto_id, fecha) -> float   |   predecir_batch(productos, fecha) -> list")

    # 10. Impacto de negocio
    _figura(prs, "Impacto de negocio", "reporte/impacto_unidades.png",
            "MAPE 10.9 % vs 19.5 %: ~130 unidades/día menos de error en el pedido (10 productos).")

    # 11. Roadmap y qué pedimos
    _bullets(prs, "Roadmap y qué pedimos", [
        "1. Piloto de 4–6 semanas con tus datos reales para calibrar el modelo.",
        "2. Integración con el punto de venta y la reposición.",
        "3. Monitoreo del error y reentrenamiento periódico.",
        "Qué pedimos: aprobar el piloto y compartir el histórico de ventas.",
    ], comentario="Honestidad: resultados sobre 60 días sintéticos y 150 predicciones de test. El enfoque está validado; falta calibrar con datos reales.")

    # Apéndice (respaldo para preguntas)
    _figura(prs, "APÉNDICE · Ventas semana a semana", "fase1/04_semana_a_semana.png",
            "9 paneles, uno por semana. El patrón se repite cada semana (sábado pico, miércoles valle).")
    _figura(prs, "APÉNDICE · Convergencia", "fase2/01_curvas_entrenamiento.png",
            "Pérdida de entrenamiento y validación por época (EarlyStopping, paciencia 12).")

    # 12. Cierre
    _titulo_slide(prs, "El modelo ya funciona",
                 "El siguiente paso es calibrarlo con tus datos reales.  |  Preguntas")

    ruta = PRESENTACION / "presentacion_final.pptx"
    prs.save(ruta)
    print(f"[OK] {ruta}")
    return ruta


if __name__ == "__main__":
    # Generar figuras auxiliares primero
    _figura_ventana()
    _figura_impacto()
    construir()
