dataset original: https://www.kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset

## FASE 1:

Generar un dataset sintético con las siguientes características:

CSVs:  
 data/inventory.csv  
 → product_id, nombre, categoria, unidad, stock_actual, fecha_expiracion

data/sales_history.csv  
 → product_id, nombre, fecha_venta, cantidad_vendida, stock_en_momento

~10 productos reales × 60 días de ventas.

Fase 1: Análisis y Preparación del Dataset

- Cargar, explorar y preparar el dataset para entrenamiento de modelos.
- Feature Engineering: Crear variables temporales relevantes (por ejemplo, día de la semana, mes, indicador de fin de semana o feriado).
- Preparar las secuencias de tiempo necesarias para el modelo (por producto o categoría).

## FASE 2:

Desarrollo y Entrenamiento de Modelos

- Diseñar y entrenar modelos predictivos
- Evaluar el modelo con métricas de calidad como RMSE
- Realizar finetuning

se tiene como referencia [CUADERNO REFERENCIA](../../materia/RNN_LSTM.ipynb)

El codigo debe ser lo mas simple y estructurado posible.
Manteniendo como guia el cuaderno de referencia.


## FASE 3:

Función de Predicción y Preparación para Despliegue
- Desarrollar una función que reciba product_id y una fecha, y devuelva la predicción de demanda para ese producto.
- Desarrollar una función que reciba un batch de productos para la misma fecha, y devuelva la lista de predicción de demanda para esa lista de productos.