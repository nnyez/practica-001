"""
Generación del reporte profesional (DOCX -> PDF) y de la presentación (PPTX -> PDF).

A partir de las figuras generadas por `analisis_exploratorio.py` y del dataset
con las variables creadas (`datos/ventas_features.csv`), este script construye:

* `reporte/reporte_tarea01.docx`  (y su PDF)
* `presentacion/presentacion_tarea01.pptx` (y su PDF)

La conversión a PDF usa LibreOffice en modo headless.

Uso:
    python src/generar_reporte.py
"""

from __future__ import annotations

import subprocess
import shutil
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from pptx import Presentation
from pptx.util import Inches as PInches
from pptx.util import Pt as PPt

import sys
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.fase1.analisis_exploratorio import (
    comparar_feriados,
    comparar_fin_de_semana,
    detectar_calidad,
    listar_feriados,
    resumen_por_categoria,
    resumen_por_producto,
)

BASE = Path(__file__).resolve().parent.parent.parent
FIG = BASE / "figuras"
REPORTE = BASE / "reporte"
PRESENTACION = BASE / "presentacion"

URL_KAGGLE = "https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset"


# --------------------------------------------------------------------------- #
# Datos
# --------------------------------------------------------------------------- #
def cargar() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ventas = pd.read_csv(BASE / "datos" / "sales_history.csv", encoding="utf-8-sig")
    inventario = pd.read_csv(BASE / "datos" / "inventory.csv", encoding="utf-8-sig")
    features = pd.read_csv(BASE / "datos" / "ventas_features.csv", encoding="utf-8-sig")
    ventas["fecha_venta"] = pd.to_datetime(ventas["fecha_venta"])
    inventario["fecha_expiracion"] = pd.to_datetime(inventario["fecha_expiracion"])
    features["fecha_venta"] = pd.to_datetime(features["fecha_venta"])
    return ventas, inventario, features


# --------------------------------------------------------------------------- #
# Helpers DOCX
# --------------------------------------------------------------------------- #
def _titulo(doc, texto, nivel=1):
    doc.add_heading(texto, level=nivel)


def _parrafo(doc, texto, negrita=False, cursiva=False):
    p = doc.add_paragraph()
    r = p.add_run(texto)
    r.bold = negrita
    r.italic = cursiva
    return p


def _vineta(doc, texto):
    doc.add_paragraph(texto, style="List Bullet")


def _figura(doc, nombre, ancho=6.3):
    ruta = FIG / nombre
    if ruta.exists():
        doc.add_picture(str(ruta), width=Inches(ancho))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        _parrafo(doc, f"[Falta la figura {nombre}]")


def _tabla_desde_df(doc, df: pd.DataFrame, titulo: str | None = None):
    if titulo:
        _parrafo(doc, titulo, negrita=True)
    tabla = doc.add_table(rows=1, cols=len(df.columns))
    tabla.style = "Light Grid Accent 1"
    for j, col in enumerate(df.columns):
        tabla.rows[0].cells[j].text = str(col)
    for _, fila in df.iterrows():
        celdas = tabla.add_row().cells
        for j, col in enumerate(df.columns):
            celdas[j].text = "" if pd.isna(fila[col]) else str(fila[col])
    return tabla


# --------------------------------------------------------------------------- #
# Construcción del DOCX
# --------------------------------------------------------------------------- #
def construir_docx(ventas, inventario, features) -> Path:
    REPORTE.mkdir(parents=True, exist_ok=True)
    doc = Document()
    est = doc.styles["Normal"].font
    est.name = "Calibri"
    est.size = Pt(11)

    # --- Portada ---
    t = doc.add_heading("Tarea 01 — Ingeniería de características", level=0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("Reporte de análisis exploratorio y variables creadas")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True
    doc.add_paragraph()

    # --- 1. Dataset ---
    _titulo(doc, "1. Dataset")
    _parrafo(doc,
             "El dataset identificado es el «Retail Store Inventory Forecasting Dataset», "
             "publicado de forma pública en Kaggle. A partir de él se construyó un dataset "
             "propio (en español) para la tarea.")
    _vineta(doc, f"Origen del dataset base: {URL_KAGGLE}")
    _vineta(doc, "Tipo: público (Kaggle) — el dataset analizado es construido a partir de él.")
    _vineta(doc, "Dataset base: 73,100 filas, 15 columnas, 5 tiendas y 20 productos (2022-2024).")

    _parrafo(doc, "Modificaciones realizadas al dataset original:", negrita=True)
    df_mod = pd.DataFrame(
        [
            ["Idioma y nombres", "Columnas y categorías en inglés genérico",
             "Se tradujo al español y se asignaron 10 productos reales de tienda de barrio."],
            ["Selección de productos", "20 product_id sin categoría asociada de forma consistente",
             "10 productos, cada uno con su categoría y unidad correctas."],
            ["Período", "731 días (2022-2024)",
             "60 días (2022-01-01 a 2022-03-01) para el análisis semana a semana."],
            ["Patrón de compras", "Datos aleatorios sin estacionalidad ni efecto feriados",
             "Se incorporó estacionalidad semanal, impulso en feriados de Ecuador y tendencia."],
            ["Estructura de archivos", "Un único archivo ancho",
             "Se separó en `inventory.csv` (catálogo) y `sales_history.csv` (ventas)."],
        ],
        columns=["Aspecto", "Dataset original", "Dataset construido"],
    )
    _tabla_desde_df(doc, df_mod)

    _parrafo(doc, "Calidad de los datos construidos:", negrita=True)
    _tabla_desde_df(doc, detectar_calidad(ventas, inventario))

    # --- 2. Análisis exploratorio ---
    _titulo(doc, "2. Análisis exploratorio y visualizaciones")
    _parrafo(doc, "Categorías de productos más importantes. Las categorías se ordenan por ventas "
                  "totales del período; Alimentos concentra la mayor parte de las ventas.")
    _figura(doc, "01_ventas_por_categoria.png")
    _tabla_desde_df(doc, resumen_por_categoria(features), "Resumen por categoría:")
    _tabla_desde_df(doc, resumen_por_producto(features), "Productos analizados:")

    _parrafo(doc, "Comportamiento de las compras a lo largo del tiempo, organizado semana a semana "
                  "durante los dos meses del período. Cada panel resume una semana y permite observar "
                  "los cambios día a día y el patrón recurrente de fin de semana.")
    _figura(doc, "03_evolucion_diaria.png")
    _figura(doc, "04_semana_a_semana.png")
    _figura(doc, "05_heatmap_semana_dia.png")
    _parrafo(doc, "Muestreo de categorías de productos para facilitar la visualización del "
                  "comportamiento conjunto a lo largo del tiempo.")
    _figura(doc, "06_categorias_en_tiempo.png")

    # --- 3. Variables creadas ---
    _titulo(doc, "3. Variables creadas")
    _parrafo(doc, "Durante la ingeniería de características se crearon las siguientes variables "
                  "temporales y de rezago:")
    df_vars = pd.DataFrame(
        [
            ["dia_semana / nombre_dia", "Numérica / texto", "Día de la semana (0=Lunes ... 6=Domingo)."],
            ["mes / dia_del_mes / anio", "Numérica", "Componentes de la fecha para capturar estacionalidad."],
            ["semana_iso / semana_del_periodo", "Numérica", "Semana del año y semana dentro del período (1..N)."],
            ["es_fin_de_semana", "Indicador (0/1)", "1 si la venta es sábado o domingo; 0 en caso contrario."],
            ["es_feriado", "Indicador (0/1)", "1 si la fecha es feriado nacional de Ecuador; 0 si no."],
            ["tipo_dia", "Categórica (4 niveles)",
             "Entre semana / Fin de semana / Feriado / Feriado (fin de semana). "
             "Sin pérdida: biyectiva con (`es_fin_de_semana`, `es_feriado`)."],
            ["ventas_dia_anterior / lag_7", "Numérica", "Ventas del día anterior y de la semana anterior por producto."],
            ["promedio_movil_7d", "Numérica", "Promedio móvil de 7 días de las ventas por producto."],
            ["dias_para_expirar", "Numérica", "Días entre la venta y la fecha de expiración del producto."],
        ],
        columns=["Variable", "Tipo", "Descripción"],
    )
    _tabla_desde_df(doc, df_vars)

    _parrafo(doc, "Efecto del fin de semana. El promedio diario de ventas es claramente mayor "
                  "los sábados y domingos, lo que confirma el patrón semanal de compras.")
    _figura(doc, "07_fin_de_semana.png")
    _tabla_desde_df(doc, comparar_fin_de_semana(features))

    _parrafo(doc, "Efecto de los feriados. Se comparan los días feriados con los días normales y se "
                  "señalan los feriados sobre la serie temporal.")
    _figura(doc, "08_feriados.png")
    _tabla_desde_df(doc, listar_feriados(features), "Feriados presentes en el período (Ecuador):")
    _tabla_desde_df(doc, comparar_feriados(features))

    _parrafo(doc, "Variables numéricas y relación stock–ventas:")
    _figura(doc, "09_distribuciones.png")
    _figura(doc, "10_stock_vs_ventas.png")

    # --- 4. Criterios y conclusiones ---
    _titulo(doc, "4. Criterios del análisis y conclusiones")
    _vineta(doc, "Las figuras muestran patrones reconocibles: pico de ventas en fin de semana y en "
                 "feriados, y una tendencia creciente leve durante el período.")
    _vineta(doc, "Cada figura incluye título y nombres en los ejes X e Y para su correcta interpretación.")
    _vineta(doc, "El negocio (tienda de barrio) explica la relevancia de las variables: fines de "
                 "semana y feriados concentran más compras, por lo que el inventario debe reforzarse esos días.")
    _vineta(doc, "Las variables creadas permiten modelar la demanda futura respetando el calendario real.")

    ruta = REPORTE / "reporte_tarea01.docx"
    doc.save(ruta)
    print(f"[OK] {ruta}")
    return ruta


# --------------------------------------------------------------------------- #
# Construcción del PPTX
# --------------------------------------------------------------------------- #
def _slide_titulo(prs, titulo, subtitulo=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # en blanco
    tb = slide.shapes.add_textbox(PInches(0.7), PInches(2.2), PInches(8.6), PInches(1.2))
    tf = tb.text_frame
    tf.text = titulo
    tf.paragraphs[0].runs[0].font.size = PPt(34)
    tf.paragraphs[0].runs[0].font.bold = True
    if subtitulo:
        p = tf.add_paragraph()
        p.text = subtitulo
        p.runs[0].font.size = PPt(16)
    return slide


def _slide_texto_bullets(prs, titulo, bullets):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    tb = slide.shapes.add_textbox(PInches(0.6), PInches(0.4), PInches(8.9), PInches(1.0))
    tb.text_frame.text = titulo
    tb.text_frame.paragraphs[0].runs[0].font.size = PPt(28)
    tb.text_frame.paragraphs[0].runs[0].font.bold = True
    body = slide.shapes.add_textbox(PInches(0.7), PInches(1.5), PInches(8.6), PInches(5.3))
    tf = body.text_frame
    tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"• {b}"
        p.font.size = PPt(18)
    return slide


def _slide_figura(prs, titulo, figura, comentario=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    tb = slide.shapes.add_textbox(PInches(0.6), PInches(0.3), PInches(8.9), PInches(0.9))
    tb.text_frame.text = titulo
    tb.text_frame.paragraphs[0].runs[0].font.size = PPt(26)
    tb.text_frame.paragraphs[0].runs[0].font.bold = True
    ruta = FIG / figura
    if ruta.exists():
        alto = PInches(5.1) if comentario is None else PInches(4.5)
        slide.shapes.add_picture(str(ruta), PInches(0.9), PInches(1.25), height=alto)
    if comentario:
        cb = slide.shapes.add_textbox(PInches(0.7), PInches(5.9), PInches(8.6), PInches(0.9))
        cb.text_frame.text = comentario
        cb.text_frame.paragraphs[0].font.size = PPt(14)
        cb.text_frame.paragraphs[0].font.italic = True
    return slide


def construir_pptx(features) -> Path:
    PRESENTACION.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    prs.slide_width = PInches(10)
    prs.slide_height = PInches(7.5)

    _slide_titulo(prs, "Ingeniería de características",
                  "Análisis exploratorio del dataset de ventas de retail — Tarea 01")

    _slide_texto_bullets(prs, "Dataset", [
        "Dataset base público de Kaggle (Retail Store Inventory Forecasting Dataset).",
        f"URL: {URL_KAGGLE}",
        "El dataset analizado es construido a partir del original.",
        "10 productos reales × 60 días (2022-01-01 a 2022-03-01).",
    ])

    _slide_texto_bullets(prs, "Modificaciones al dataset", [
        "Traducción al español y productos reales con su categoría y unidad.",
        "Recorte del período a dos meses para el análisis semana a semana.",
        "Incorporación de estacionalidad semanal y efecto de feriados de Ecuador.",
        "Separación en inventory.csv (catálogo) y sales_history.csv (ventas).",
    ])

    _slide_texto_bullets(prs, "Variables creadas", [
        "Temporales: mes, día de la semana, semana del período, semana ISO.",
        "Fin de semana: variable indicadora es_fin_de_semana (0/1).",
        "Feriados: variable indicadora es_feriado (0/1) con feriados de Ecuador.",
        "Rezagos: ventas del día anterior, de hace 7 días y promedio móvil de 7 días.",
    ])

    _slide_figura(prs, "Categorías más importantes", "01_ventas_por_categoria.png",
                  "Alimentos concentra la mayor parte de las ventas del período.")
    _slide_figura(prs, "Ventas semana a semana", "04_semana_a_semana.png",
                  "Se observa el patrón recurrente de mayor compra en fin de semana.")
    _slide_figura(prs, "Muestreo de categorías en el tiempo", "06_categorias_en_tiempo.png",
                  "Evolución diaria de una muestra de categorías.")
    _slide_figura(prs, "Fin de semana vs. entre semana", "07_fin_de_semana.png",
                  "El fin de semana vende más que los días entre semana.")
    _slide_figura(prs, "Influencia de los feriados", "08_feriados.png",
                  "Los feriados presentan un promedio diario de ventas superior al de los días normales.")

    _slide_texto_bullets(prs, "Conclusiones", [
        "Existen patrones reconocibles: fin de semana y feriados elevan las ventas.",
        "El conocimiento del negocio (tienda de barrio) guía las variables creadas.",
        "Las variables permiten anticipar la demanda y planificar el inventario.",
    ])

    ruta = PRESENTACION / "presentacion_tarea01.pptx"
    prs.save(ruta)
    print(f"[OK] {ruta}")
    return ruta


# --------------------------------------------------------------------------- #
# Conversión a PDF
# --------------------------------------------------------------------------- #
def convertir_pdf(ruta: Path) -> None:
    """Convierte un .docx/.pptx a PDF usando LibreOffice headless."""
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


# --------------------------------------------------------------------------- #
# Punto de entrada
# --------------------------------------------------------------------------- #
def main() -> None:
    ventas, inventario, features = cargar()
    docx = construir_docx(ventas, inventario, features)
    pptx = construir_pptx(features)
    convertir_pdf(docx)
    convertir_pdf(pptx)


if __name__ == "__main__":
    main()
