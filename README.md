# Tarea 01 — Ventas retail: datos, modelos y predicción

Proyecto de series de tiempo sobre las ventas diarias de una tienda de barrio.
Incluye el análisis y la ingeniería de características, el entrenamiento de
modelos LSTM y las funciones de predicción listas para despliegue.

## Contenido

| Ruta | Descripción |
|---|---|
| `datos/original-dataset.csv` | Dataset base público de Kaggle (fuente). |
| `datos/inventory.csv` | Catálogo de productos (dataset construido). |
| `datos/sales_history.csv` | Historial de ventas (dataset construido). |
| `datos/ventas_features.csv` | Ventas con las variables creadas. |
| `notebooks/tarea01_ingenieria_caracteristicas.ipynb` | EDA, variables y secuencias. |
| `notebooks/fase2_modelos.ipynb` | Modelo LSTM, finetuning y evaluación. |
| `notebooks/fase3_prediccion.ipynb` | Funciones de predicción y despliegue. |
| `src/fase1/generar_dataset.py` | Genera el dataset sintético con patrones realistas. |
| `src/fase1/analisis_exploratorio.py` | Funciones del análisis exploratorio (EDA). |
| `src/fase1/feature_engineering.py` | Crea las variables de ingeniería de características. |
| `src/fase1/generar_reporte.py` | Construye el reporte (DOCX/PDF) y la presentación (PPTX/PDF). |
| `src/fase2/` | Modelos predictivos (RNN/LSTM). |
| `src/fase2/config.py` | Rutas e hiperparámetros. |
| `src/fase2/datos.py` | Carga, escalado y secuencias temporales. |
| `src/fase2/modelos.py` | Constructores RNN / LSTM / LSTM apilada. |
| `src/fase2/entrenamiento.py` | Entrenamiento con EarlyStopping y finetuning. |
| `src/fase2/evaluacion.py` | Métricas (RMSE/MAE/MAPE) y figuras. |
| `src/fase2/ejecutar.py` | Pipeline completo de modelos (CLI). |
| `src/fase3/` | Función de predicción y despliegue. |
| `src/fase3/config.py` | Rutas y constantes. |
| `src/fase3/modelo.py` | Carga del modelo `.keras` y escalador. |
| `src/fase3/entrada.py` | Construcción de la ventana de 7 días. |
| `src/fase3/prediccion.py` | Funciones `predecir_venta` y `predecir_batch`. |
| `src/fase3/ejecutar.py` | CLI de prueba. |
| `scripts/` | Generadores de notebooks (`build_notebook_fase2.py`, `build_notebook_fase3.py`). |
| `figuras/fase2/` | Figuras de evaluación del modelo. |
| `_referencia/` | Material auxiliar del usuario (análisis previo, hoja de cálculo). |
| `resultados/fase2/` | Métricas e historiales de entrenamiento. |
| `modelos/fase2/` | Modelo LSTM final guardado (.keras). |
| `figuras/` | Figuras del EDA de la Fase 1. |
| `reporte/` | Reporte profesional en DOCX y PDF. |
| `presentacion/` | Presentación en PPTX y PDF. |
| `presentacion/guia_presentacion.md` | Guion cronometrado (5 min) + preguntas frecuentes y checklist. |

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

# 2) Generar las figuras del EDA y ver el perfil de los datos
.venv/bin/python src/fase1/analisis_exploratorio.py

# 3) Crear las variables de ingeniería de características
.venv/bin/python src/fase1/feature_engineering.py

# 4) Generar el reporte (PDF) y la presentación (PDF/PPTX)
.venv/bin/python src/fase1/generar_reporte.py
```

### Modelos predictivos

```bash
# Entrenar modelos (RNN, LSTM, LSTM apilada), hacer finetuning,
# evaluar con RMSE/MAE/MAPE y guardar métricas, figuras y modelo
.venv/bin/python -m src.fase2.ejecutar
```

> El notebook `fase2_modelos.ipynb` y este comando generan los mismos
> artefactos (`metricas.csv`, figuras y modelo). Ejecuta uno de los dos para
> mantener métricas y figuras consistentes entre sí.

### Predicción y despliegue

```bash
# Probar funciones de predicción individual y en lote
.venv/bin/python -m src.fase3.ejecutar
```
