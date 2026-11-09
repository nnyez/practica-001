# Tarea 01 — Ventas retail: datos, modelos y predicción

Proyecto de series de tiempo sobre las ventas diarias de una tienda de barrio.
Incluye el análisis y la ingeniería de características, el entrenamiento de un
modelo LSTM (red neuronal recurrente) y las funciones de predicción listas para
despliegue, con una interfaz web sencilla.

## Estructura

```
docs/                      instrucciones, requisitos y guías
datos/                     datasets generados (inventory, sales_history, ventas_features)
referencia/                material auxiliar (dataset original, notebooks modificados, Data.ods)
src/fase1/                 datos, EDA, feature engineering y generación de reportes
src/fase2/                 modelo LSTM (entrenamiento, evaluación, finetuning)
src/fase3/                 funciones de predicción (predecir_venta, predecir_batch)
app/                       interfaz web (HTML) de la Fase 3
notebooks/                 los 3 notebooks finales
scripts/                   generadores de notebooks
figuras/fase1/             figuras del EDA
figuras/fase2/             figuras de evaluación del modelo
figuras/reporte/           figuras auxiliares de los reportes
modelos/fase2/             modelo LSTM final (.keras) y escalador
resultados/fase2/          métricas e historiales de entrenamiento
reporte/                   reportes en DOCX/PDF
presentacion/              presentaciones en PPTX/PDF y guiones
```

## Contenido principal

| Ruta | Descripción |
|---|---|
| `docs/initial-instructions.md` | Enunciado de las 3 fases. |
| `docs/tarea01-requisitos.md` | Rúbrica de la Tarea 01. |
| `docs/GUIA_FASE3.md` | Guía de la Fase 3: funciones y despliegue. |
| `datos/inventory.csv` | Catálogo de productos (dataset construido). |
| `datos/sales_history.csv` | Historial de ventas (dataset construido). |
| `datos/ventas_features.csv` | Ventas con las variables creadas. |
| `referencia/original-dataset.csv` | Dataset base público de Kaggle (fuente). |
| `notebooks/fase1_ingenieria_caracteristicas.ipynb` | EDA, variables y secuencias. |
| `notebooks/fase2_modelos.ipynb` | Modelo LSTM, finetuning y evaluación. |
| `notebooks/fase3_prediccion.ipynb` | Funciones de predicción y despliegue. |
| `src/fase1/generar_dataset.py` | Genera el dataset sintético con patrones realistas. |
| `src/fase1/analisis_exploratorio.py` | Funciones del análisis exploratorio (EDA). |
| `src/fase1/feature_engineering.py` | Crea las variables de ingeniería de características. |
| `src/fase1/generar_reporte.py` | Reporte académico (DOCX/PDF) y presentación de avance. |
| `src/fase1/generar_reporte_cliente.py` | Reporte completo para el cliente (DOCX/PDF). |
| `src/fase1/generar_reporte_cliente_corto.py` | Reporte corto para el cliente (DOCX/PDF). |
| `src/fase1/generar_presentacion_final.py` | Presentación final de las 3 fases (PPTX/PDF). |
| `src/fase2/config.py` | Rutas e hiperparámetros. |
| `src/fase2/datos.py` | Carga, escalado y secuencias temporales. |
| `src/fase2/modelos.py` | Constructor del modelo LSTM (RNN). |
| `src/fase2/entrenamiento.py` | Entrenamiento con EarlyStopping y finetuning. |
| `src/fase2/evaluacion.py` | Métricas (RMSE/MAE/MAPE) y figuras. |
| `src/fase2/ejecutar.py` | Pipeline completo de modelos (CLI). |
| `src/fase3/config.py` | Rutas y constantes. |
| `src/fase3/modelo.py` | Carga del modelo `.keras` y escalador. |
| `src/fase3/entrada.py` | Construcción de la ventana de 7 días. |
| `src/fase3/prediccion.py` | Funciones `predecir_venta` y `predecir_batch`. |
| `src/fase3/ejecutar.py` | CLI de prueba. |
| `app/app.py` | Servidor web con la interfaz HTML de predicción. |
| `app/templates/index.html` | Plantilla HTML de la interfaz. |
| `scripts/` | Generadores de notebooks (`build_notebook_fase2.py`, `build_notebook_fase3.py`). |
| `reporte/reporte_tarea01.docx` | Reporte académico de la Tarea 01 (DOCX/PDF). |
| `reporte/reporte_cliente.docx` | Reporte ejecutivo para el cliente (DOCX/PDF). |
| `reporte/reporte_cliente_corto.docx` | Reporte corto para el cliente (DOCX/PDF). |
| `presentacion/presentacion_tarea01.pptx` | Presentación de avance (Tarea 01, 5 min). |
| `presentacion/presentacion_final.pptx` | Presentación final de resultados (3 fases, 10 min). |
| `presentacion/guia_presentacion.md` | Guion cronometrado (5 min) + preguntas frecuentes. |
| `presentacion/guia_presentacion_final.md` | Guion cronometrado (10 min) + preguntas frecuentes. |

## Dataset

- **URL de origen:** https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset
- **Tipo:** el dataset base es **público** (Kaggle); el dataset analizado es **construido**
  a partir de él (10 productos reales × 60 días, en español, con estacionalidad semanal
  y feriados de Ecuador). Las modificaciones se detallan en el reporte.

## Entorno

Requiere Python 3.12 (gestionado con `pyenv`).

```bash
pyenv local 3.12.7
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Reproducir el análisis

### Datos, EDA y variables

```bash
# 1) Generar el dataset sintético
.venv/bin/python src/fase1/generar_dataset.py

# 2) Generar las figuras del EDA (figuras/fase1/) y ver el perfil de los datos
.venv/bin/python src/fase1/analisis_exploratorio.py

# 3) Crear las variables de ingeniería de características
.venv/bin/python src/fase1/feature_engineering.py

# 4) Generar el reporte académico y la presentación de avance
.venv/bin/python src/fase1/generar_reporte.py

# 5) Generar los reportes para el cliente
.venv/bin/python src/fase1/generar_reporte_cliente.py
.venv/bin/python src/fase1/generar_reporte_cliente_corto.py

# 6) Generar la presentación final de las 3 fases
.venv/bin/python src/fase1/generar_presentacion_final.py
```

### Modelos predictivos

```bash
# Entrenar el modelo LSTM (RNN), hacer finetuning,
# evaluar con RMSE/MAE/MAPE y guardar métricas, figuras y modelo
.venv/bin/python -m src.fase2.ejecutar
```

> El notebook `fase2_modelos.ipynb` y este comando generan los mismos
> artefactos (`metricas.csv`, figuras y modelo). Ejecuta uno de los dos para
> mantener métricas y figuras consistentes entre sí.

### Predicción y despliegue

```bash
# Probar funciones de predicción individual y en lote (CLI)
.venv/bin/python -m src.fase3.ejecutar

# Levantar la interfaz web de predicción (HTML)
.venv/bin/python -m app.app
# -> abrir http://127.0.0.1:8000 en el navegador
```

La interfaz web expone las dos funciones de la Fase 3:

| Ruta | Método | Entrada | Salida |
|---|---|---|---|
| `/` | GET | — | Página con los dos formularios |
| `/predecir` | POST | `producto_id`, `fecha` | Predicción individual |
| `/predecir_lote` | POST | `productos`, `fecha` | Tabla de predicciones |

> El comando de la interfaz se ejecuta **desde la raíz del proyecto** para que
> los paquetes `app` y `src` sean importables.
