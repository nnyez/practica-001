# Guía de la Fase 3 — Función de predicción y despliegue

La Fase 3 entrega las dos funciones exigidas y una interfaz web sencilla para usarlas.

## 1. Qué exige el enunciado

> - Desarrollar una función que reciba `product_id` y una fecha, y devuelva la predicción de demanda para ese producto.
> - Desarrollar una función que reciba un batch de productos para la misma fecha, y devuelva la lista de predicción de demanda para esa lista de productos.

## 2. Las dos funciones (ya implementadas)

Viven en `src/fase3/prediccion.py` y son la base de todo lo demás:

```python
from src.fase3 import predecir_venta, predecir_batch

predecir_venta("P0008", "2022-03-02")
# -> 165.34  (unidades reales)

predecir_batch(["P0001", "P0005", "P0008", "P0009"], "2022-03-02")
# -> [{'producto_id': 'P0001', 'fecha': '2022-03-02', 'prediccion': 123.4}, ...]
```

**Contratos:**

| Función | Entrada | Salida | Errores |
|---|---|---|---|
| `predecir_venta` | `product_id: str`, `fecha` | `float` (unidades) | `ValueError` si el producto no existe o no hay 7 días de historial |
| `predecir_batch` | `productos: list[str]`, `fecha` | `list[dict]` con `prediccion` o `error` | No interrumpe el lote: cada fallo va en su propio dict con clave `error` |

## 3. Cómo funciona por dentro

```
producto_id + fecha
        │
        ▼
src/fase3/entrada.py  →  construir_ventana()
        │  toma los 7 días ANTERIORES de ese producto
        │  y arma la matriz (7, 15):
        │     col 0        cantidad_vendida
        │     col 1        es_fin_de_semana
        │     col 2        es_feriado
        │     col 3-4      dia_sin, dia_cos  (ciclo de la semana)
        │     col 5-14     one-hot del producto (10 productos)
        ▼
src/fase3/modelo.py   →  predecir_ventana()
        │  escala con el MinMaxScaler guardado en el entrenamiento
        │  pasa la ventana por el LSTM
        │  desescala la salida a unidades reales
        ▼
predicción en unidades
```

Piezas involucradas:

| Archivo | Responsabilidad |
|---|---|
| `src/fase3/config.py` | Rutas (modelo `.keras`, escalador `.pkl`, datos) y `VENTANA = 7` |
| `src/fase3/modelo.py` | Carga perezosa del modelo y el escalador; escala/predice/desescala |
| `src/fase3/entrada.py` | Construye la ventana `(7, 15)` en el mismo orden que el entrenamiento |
| `src/fase3/prediccion.py` | API pública: `predecir_venta`, `predecir_batch` |
| `app/app.py` | Servidor web con la interfaz HTML |
| `app/templates/index.html` | Plantilla de la interfaz |

Detalle importante: **el escalador no se recalcula**. Se carga el `escalador.pkl` que se ajustó con el conjunto de entrenamiento. Reconstruirlo sería incorrecto en despliegue.

## 4. La interfaz web (HTML)

`app/app.py` levanta un servidor con la librería estándar (`http.server`), sin dependencias adicionales.

### Arrancar

```bash
.venv/bin/python -m app.app
```

Salida esperada:

```
======================================================================
  Predicción de demanda — Fase 3 (interfaz web)
======================================================================
  Abre en el navegador:  http://127.0.0.1:8000
  Productos disponibles: 10
  Fechas admitidas:      2022-01-08 a 2023-03-01
  Ctrl+C para detener.
======================================================================
```

Opciones: `--host` (por defecto `127.0.0.1`) y `--puerto` (por defecto `8000`).

### La página

Dos formularios sobre la misma pantalla:

1. **Predicción individual** — dropdown con los 10 productos (`P0001 — Arroz blanco`, …), date picker y botón *Predecir*. Devuelve la demanda estimada en unidades.
2. **Predicción en lote** — textarea (un `product_id` por línea, también acepta comas), date picker y botón *Predecir lote*. Devuelve el total del lote y una tabla producto → predicción.

Debajo, el área de **Resultado** muestra la última predicción, o el error si no se pudo calcular.

### Rutas HTTP

| Ruta | Método | Formato | Respuesta |
|---|---|---|---|
| `/` | GET | — | Página HTML con los formularios |
| `/predecir` | POST | `producto_id=...&fecha=YYYY-MM-DD` | HTML con la predicción individual |
| `/predecir_lote` | POST | `productos=...&fecha=YYYY-MM-DD` | HTML con la tabla de predicciones |
| cualquier otra | GET/POST | — | 404 |

### Límites y errores (mostrados en la interfaz)

| Situación | Mensaje |
|---|---|
| Producto inexistente | `Producto 'XXXX' no encontrado en los datos.` |
| Fecha sin 7 días previos | `Se requieren 7 días de historial para P0001 antes de 2022-01-03; solo hay 2.` |
| Lote con productos inválidos | Se predicen los válidos y los fallidos aparecen con su error, sin cortar el lote |

La fecha se valida en el formulario: el mínimo es el primer día con 7 días de historial (`2022-01-08`) y el máximo es un año después del último dato real.

## 5. Prueba por línea de comandos

Sin navegador, para verificar rápido:

```bash
.venv/bin/python -m src.fase3.ejecutar
```

```
======================================================================
Predicción de demanda
======================================================================
P0001 para 2022-03-02: 123.42 unidades

Lote para 2022-03-02:
  P0001: 123.42 unidades
  ...
```

## 6. Verificación realizada

| Prueba | Resultado |
|---|---|
| `GET /` | 200, HTML con los 10 productos en el dropdown |
| `POST /predecir` (P0008, 2022-03-02) | 165 unidades |
| `POST /predecir_lote` (4 productos) | 4 de 4 predichos, total 574 unidades |
| Producto inexistente | Mensaje de error, sin caída |
| Fecha sin historial suficiente | Mensaje de error, sin caída |
| Lote mixto (1 válido + 1 inválido) | 1 de 2 predichos, el inválido reportado |
| Marcadores `{{...}}` sin resolver | Ninguno |
| Ruta inexistente | 404 |

## 7. Estructura resultante de la Fase 3

La lógica de predicción queda separada de la capa de despliegue (HTML):

```
src/fase3/                 # lógica de predicción
├── __init__.py
├── config.py              rutas y constantes
├── modelo.py              carga del LSTM y el escalador
├── entrada.py             construcción de la ventana de 7 días
├── prediccion.py          predecir_venta() y predecir_batch()
└── ejecutar.py            prueba por CLI

app/                       # capa de despliegue (interfaz web)
├── __init__.py
├── app.py                 servidor HTTP y rutas
└── templates/
    └── index.html         plantilla de la interfaz
```

La interfaz no duplica lógica: importa `predecir_venta` y `predecir_batch` desde `src/fase3/`, que son las mismas funciones exigidas por el enunciado y las que usa el notebook `fase3_prediccion.ipynb`.

> El comando de arranque se ejecuta **desde la raíz del proyecto** para que el paquete `app` y `src` sean importables.
