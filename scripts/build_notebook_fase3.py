#!/usr/bin/env python3
"""Genera el notebook investigativo de predicción y despliegue."""
from pathlib import Path
import nbformat as nbf

base = Path(__file__).resolve().parent.parent
nb = nbf.v4.new_notebook()
cells = []

def md(src): cells.append(nbf.v4.new_markdown_cell(src))
def code(src): cells.append(nbf.v4.new_code_cell(src))

# ============================ 0. TÍTULO ============================
md("""# Tarea 01: Función de Predicción y Despliegue

**Universidad / Automatización**  
**Dataset base:** [Retail Store Inventory Forecasting Dataset - Kaggle](https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset)

**Objetivo:** Desarrollar funciones que reciban un `product_id` y una fecha (o un lote de productos para una misma fecha) y devuelvan la predicción de demanda usando el modelo LSTM entrenado en la fase anterior.

---

## Índice

- [1. Objetivos y alcance](#1-objetivos-y-alcance)
- [2. Setup del entorno](#2-setup-del-entorno)
- [3. Carga del modelo y el escalador](#3-carga-del-modelo-y-el-escalador)
- [4. Construcción de la ventana de entrada](#4-construcción-de-la-ventana-de-entrada)
- [5. Predicción individual: `predecir_venta`](#5-predicción-individual-predecir_venta)
- [6. Predicción en lote: `predecir_batch`](#6-predicción-en-lote-predecir_batch)
- [7. Comparación con valor real](#7-comparación-con-valor-real)
- [8. Casos de error](#8-casos-de-error)
- [9. Conclusiones](#9-conclusiones)
- [10. Anexo: reproducibilidad](#10-anexo-reproducibilidad)
""")

# ============================ 1. OBJETIVOS ============================
md("""## 1. Objetivos y alcance

Requisitos a cumplir:

- [x] Función que recibe `product_id` y una fecha y devuelve la predicción de demanda.
- [x] Función que recibe un lote de productos para la misma fecha y devuelve la lista de predicciones.
- [x] Usar el modelo LSTM entrenado en la fase anterior (`modelos/fase2/lstm_final.keras`).
- [x] Código simple y estructurado, en el paquete `src/fase3/`.

**Flujo:**

```
producto_id + fecha
        │
        ▼
últimos 7 días de historial  →  ventana (7, 15)
        │
        ▼
escalar (0-1)  →  LSTM  →  desescalar  →  unidades reales
```
""")

# ============================ 2. SETUP ============================
md("""## 2. Setup del entorno""")

code("""import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # silencia logs de TensorFlow

import sys
from pathlib import Path

BASE = Path('..').resolve()
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

import pandas as pd

from src.fase3 import inicializar, predecir_batch, predecir_venta
from src.fase3.config import RUTA_DATOS
from src.fase3.entrada import construir_ventana, ventana_disponible

print('Entorno listo.')
""")

# ============================ 3. CARGA ============================
md("""## 3. Carga del modelo y el escalador

El LSTM se entrenó con las 15 variables escaladas entre 0 y 1. El escalador se carga desde `modelos/fase2/escalador.pkl` (guardado en el entrenamiento), no se reconstruye. La carga es automática la primera vez que se predice; aquí se hace explícita para dejarlo claro.""")

code("""inicializar()
print('Modelo y escalador cargados.')
print('Ventana esperada:', 7, 'días')
""")

# ============================ 4. VENTANA ============================
md("""## 4. Construcción de la ventana de entrada

Para predecir una fecha se toman los 7 días anteriores de ese producto. Cada fila contiene: `cantidad_vendida`, `es_fin_de_semana`, `es_feriado`, `dia_sin`, `dia_cos` y el one-hot del producto (15 columnas en total).""")

code("""df = pd.read_csv(RUTA_DATOS, encoding='utf-8-sig', parse_dates=['fecha_venta'])

producto, fecha = 'P0001', '2022-03-02'
print('¿Ventana disponible?', ventana_disponible(df, producto, fecha))

X = construir_ventana(df, producto, fecha)
print('Forma:', X.shape)
print('Primera fila:', X[0])
print('Última fila :', X[-1])
""")

# ============================ 5. INDIVIDUAL ============================
md("""## 5. Predicción individual: `predecir_venta`""")

code("""for producto in ['P0001', 'P0008']:
    print(f'{producto} 2022-03-02: {predecir_venta(producto, "2022-03-02"):.2f} unidades')
""")

# ============================ 6. BATCH ============================
md("""## 6. Predicción en lote: `predecir_batch`

Recibe una lista de productos para la misma fecha. Si un producto falla, se registra el error sin interrumpir el resto.""")

code("""for r in predecir_batch(['P0001', 'P0002', 'P0003', 'P0008', 'P0010'], '2022-03-02'):
    print(r)
""")

# ============================ 7. COMPARACIÓN ============================
md("""## 7. Comparación con valor real

Se predice una fecha del historial (2022-02-28) y se compara con la venta real registrada.""")

code("""fecha, producto = pd.Timestamp('2022-02-28'), 'P0001'

prediccion = predecir_venta(producto, fecha)
real = float(df.loc[(df['product_id'] == producto) & (df['fecha_venta'] == fecha), 'cantidad_vendida'].iloc[0])

print(f'{producto} {fecha.date()}')
print(f'  Predicción: {prediccion:.2f}')
print(f'  Real      : {real:.2f}')
print(f'  Error     : {abs(prediccion - real):.2f} unidades ({abs(prediccion - real) / real * 100:.1f}%)')
""")

# ============================ 8. ERRORES ============================
md("""## 8. Casos de error

- Producto inexistente.
- Fecha sin 7 días de historial previo.
- Lote mixto: los productos válidos se predicen y los inválidos se reportan.""")

code("""for producto, fecha in [('P9999', '2022-03-02'), ('P0001', '2022-01-05')]:
    try:
        predecir_venta(producto, fecha)
    except ValueError as exc:
        print(f'{producto} {fecha} -> {exc}')

print()
for r in predecir_batch(['P0001', 'P9999', 'P0002'], '2022-03-02'):
    print(r)
""")

# ============================ 9. CONCLUSIONES ============================
md("""## 9. Conclusiones

- `predecir_venta` y `predecir_batch` quedan listas para usarse en despliegue.
- Reutilizan el modelo y el escalador entrenados antes, sin reentrenar.
- El lote tolera productos inválidos sin detener el resto.
- El modelo necesita los 7 días previos reales, por lo que sirve para predicción diaria con datos actualizados.
""")

# ============================ 10. ANEXO ============================
md("""## 10. Anexo: reproducibilidad

```bash
.venv/bin/python -m src.fase3.ejecutar
```

**Módulos:**

- `src/fase3/modelo.py` — carga del LSTM y del escalador guardados.
- `src/fase3/entrada.py` — construcción de la ventana.
- `src/fase3/prediccion.py` — funciones públicas.
- `src/fase3/ejecutar.py` — CLI de prueba.
""")

nb['cells'] = cells
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12.7"},
}

out = base / 'notebooks' / 'fase3_prediccion.ipynb'
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print('Notebook generado:', out)
print('Celdas:', len(nb.cells))
