"""
Reporte corto para el cliente (primera impresión): máx. 3 páginas.
Versión con más gráficas.

Uso:
    python src/fase1/generar_reporte_cliente_corto.py
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

BASE = Path(__file__).resolve().parent.parent.parent
FIG = BASE / "figuras"
REPORTE = BASE / "reporte"

URL_KAGGLE = "https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset"


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


def _figura(doc, nombre, ancho=5.0):
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


def construir() -> Path:
    REPORTE.mkdir(parents=True, exist_ok=True)
    doc = Document()
    est = doc.styles["Normal"].font
    est.name = "Calibri"
    est.size = Pt(10)

    # --- Título ---
    t = doc.add_heading("Predicción de demanda para reducir quiebres de stock", level=0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("Reporte para el cliente · Solución de predicción de demanda diaria")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True
    doc.add_paragraph()

    # --- 1. Resumen ejecutivo ---
    _titulo(doc, "1. Resumen ejecutivo")
    _parrafo(doc, "Hoy la tienda repone 'a ojo': quiebres de stock en fin de semana y sobrestock entre semana. "
                  "La demanda tiene un patrón claro que se puede predecir con un error del 10.9 %.")
    _vineta(doc, "El fin de semana vende un 55.6 % más que entre semana; los feriados, un 40.1 % más.")
    _vineta(doc, "El modelo reduce el error de pronóstico de 19.5 % a 10.9 % (un 45 % menos).")
    _vineta(doc, "Eso equivale a unas 130 unidades menos de error al día en la tienda (10 productos).")
    _parrafo(doc, "Pedido: aprobar un piloto de 4 a 6 semanas con datos reales y compartir el histórico de ventas.",
             negrita=True)

    # --- 2. El problema ---
    _titulo(doc, "2. El problema del negocio")
    _parrafo(doc, "En una tienda de barrio la reposición se hace por intuición. Cuando la demanda sube (fin de semana, "
                  "feriados) hay quiebre de stock y se pierden ventas; cuando baja, hay capital inmovilizado. "
                  "La pregunta que el modelo responde: ¿cuánto venderé mañana de cada producto?")

    # --- 3. La solución ---
    _titulo(doc, "3. La solución")
    _parrafo(doc, "Construimos un modelo que estima la demanda diaria por producto usando el historial de ventas y el "
                  "calendario. Mira los últimos 7 días de cada producto y estima la venta del día siguiente.")

    # --- 4. Los datos ---
    _titulo(doc, "4. Los datos")
    _parrafo(doc, "Origen: dataset público de Kaggle. El dataset analizado fue construido: 10 productos reales × 60 días "
                  "(1 ene – 1 mar 2022). Modificaciones: traducido al español, productos reales, período de 2 meses, "
                  "patrón semanal y feriados de Ecuador.")
    _vineta(doc, "Categorías: Alimentos (49.6 %), Bebidas (14.0 %), Snacks (13.2 %), Cuidado personal (8.2 %), Hogar (7.7 %), Limpieza (7.3 %).")
    _vineta(doc, "Productos: Arroz, Leche, Pan, Aceite, Huevos, Detergente, Jabón, Agua, Galletas, Papel higiénico.")

    # --- 5. Lo que encontramos ---
    _titulo(doc, "5. Lo que encontramos")
    _vineta(doc, "Sábado: 2.183 unidades/día (pico). Miércoles: 1.117 unidades/día (valle).")
    _vineta(doc, "Fin de semana vende un 55.6 % más que entre semana.")
    _vineta(doc, "Feriados venden un 40.1 % más (3 feriados en la ventana: 1 ene, 28 feb, 1 mar).")
    _vineta(doc, "Alimentos concentra el 49.6 % de las ventas; Bebidas y Snacks son los más rotativos por producto.")
    _figura(doc, "fase1/07_fin_de_semana.png", ancho=4.0)
    _figura(doc, "fase1/08_feriados.png", ancho=4.0)

    # --- 6. Resultados del modelo ---
    _titulo(doc, "6. Resultados del modelo")
    df_res = pd.DataFrame(
        [
            ["Método actual (repetir venta de ayer)", 44.12, 32.43, 19.54],
            ["Modelo predictivo", 24.28, 17.97, 10.88],
        ],
        columns=["Método", "Error RMSE", "Error MAE", "Error MAPE (%)"],
    )
    _tabla(doc, df_res, tamano=9)
    _parrafo(doc, "El modelo reduce el error un 45 %.", negrita=True)
    _figura(doc, "reporte/forecast_futuro.png", ancho=5.0)
    _parrafo(doc, "Ventas reales (línea sólida) y predicciones del modelo (línea discontinua) que se extienden "
                  "más allá de los valores reales. La línea vertical marca el último dato real.", cursiva=True, tamano=8.5)

    # --- 7. Impacto y pedido ---
    _titulo(doc, "7. Impacto y qué pedimos")
    _vineta(doc, "Venta media por producto y día: 151 unidades.")
    _vineta(doc, "Error por producto y día: 16 unidades (modelo) vs 29 (método actual).")
    _vineta(doc, "En la tienda: unas 130 unidades diarias menos de error en el pedido.")
    _vineta(doc, "Beneficio: menos quiebres en fin de semana y feriados, menos capital inmovilizado entre semana.")
    _figura(doc, "reporte/impacto_unidades.png", ancho=4.0)
    _parrafo(doc, "Pedido: aprobar un piloto de 4 a 6 semanas con datos reales y compartir el histórico de ventas.",
             negrita=True)
    _parrafo(doc, "Nota: resultados sobre 60 días sintéticos. El enfoque está validado; falta calibrarlo con datos reales. "
                  "La traducción a dinero es ilustrativa (supuesto de precio promedio).", cursiva=True, tamano=8.5)

    ruta = REPORTE / "reporte_cliente_corto.docx"
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
    construir()
    convertir_pdf(REPORTE / "reporte_cliente_corto.docx")


if __name__ == "__main__":
    main()
