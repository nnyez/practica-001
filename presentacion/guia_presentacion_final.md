# Guía de exposición — Presentación final (3 fases)

**Tiempo objetivo: 10 minutos (≈50 s por diapositiva).**
Material: `presentacion/presentacion_final.pptx` (o `.pdf`). Apéndice al final para preguntas.
Reporte de respaldo: `reporte/reporte_tarea01.pdf` (Fase 1) + el futuro reporte para el cliente.

---

## Cronograma

| # | Diapositiva | Tiempo | Figura |
|---|---|---|---|
| 1 | Portada | 0:00 – 0:15 | — |
| 2 | El problema y la propuesta | 0:15 – 1:00 | — |
| 3 | FASE 1 · El dataset | 1:00 – 1:35 | — |
| 4 | FASE 1 · Qué encontramos | 1:35 – 2:20 | `11_tres_categorias_por_semana.png` + `08_feriados.png` |
| 5 | FASE 1 · Variables y secuencias | 2:20 – 3:00 | — |
| 6 | FASE 2 · Cómo modelamos | 3:00 – 3:35 | `ventana_7dias.png` |
| 7 | FASE 2 · Resultados | 3:35 – 4:30 | tabla + `fase2/03_comparacion_modelos.png` |
| 8 | FASE 2 · ¿Es confiable? | 4:30 – 5:10 | `fase2/02_prediccion_vs_real.png` |
| 9 | FASE 3 · Cómo se usa | 5:10 – 6:05 | `fase2/04_prediccion_producto.png` |
| 10 | Impacto de negocio | 6:05 – 7:05 | `impacto_unidades.png` |
| 11 | Roadmap y qué pedimos | 7:05 – 8:15 | — |
| 12 | Cierre | 8:15 – 8:40 | — |
| A1 | APÉNDICE · Semana a semana | (solo si preguntan) | `04_semana_a_semana.png` |
| A2 | APÉNDICE · Convergencia | (solo si preguntan) | `fase2/01_curvas_entrenamiento.png` |

> Margen: ~1:20 para transiciones y preguntas cortas. Si vas apretado, salta la lámina 8 (confiabilidad) y la A1/A2.

---

## Guion diapositiva por diapositiva

### 1. Portada (0:00 – 0:15)
> "Buenos días. Esta presentación resume tres fases de trabajo sobre las ventas de una tienda
> de barrio: de los datos crudos a un modelo que predice la demanda diaria por producto."

### 2. El problema y la propuesta (0:15 – 1:00)
> "Hoy la tienda repone a ojo: quiebres de stock en fin de semana y sobrestock entre semana.
> La demanda no es plana — el fin de semana vende un 55.6 % más y los feriados un 40.1 % más.
> La propuesta es predecir la demanda diaria por producto, para decidir cuánto stock tener.
> El objetivo de negocio: menos quiebres, menos capital inmovilizado, mejor servicio."

### 3. FASE 1 · El dataset (1:00 – 1:35)
> "El dataset de partida es público, de Kaggle: Retail Store Inventory Forecasting.
> URL: kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset.
> Ese dataset tiene 73 mil filas, pero es genérico y no permite un análisis de tienda.
> El dataset que analizo es construido: diez productos reales por sesenta días — del 1 de enero
> al 1 de marzo de 2022.
> Modificaciones: traducido al español, productos reales, período de dos meses, patrón semanal
> y feriados de Ecuador. El original es aleatorio: `Holiday/Promotion` no influye en las ventas
> (136.5 vs 136.4) y las fechas vienen en formato mezclado."

**Cifras:** 73,100 filas (original) · 10 productos × 60 días = 600 registros (construido).

### 4. FASE 1 · Qué encontramos (1:35 – 2:20)
> "El patrón se repite cada semana: sábado pico de 2,183 unidades y miércoles valle de 1,117.
> Tres categorías más importantes: Alimentos con el 49.6 %, Bebidas con el 14.0 % y Snacks
> con el 13.2 %. Y los feriados elevan las ventas un 40.1 %."

**Cifras por día de la semana (promedio diario, toda la tienda):**

| Sábado | Domingo | Viernes | Lunes | Martes | Jueves | Miércoles |
|---|---|---|---|---|---|---|
| 2,183 | 1,851 | 1,511 | 1,347 | 1,262 | 1,241 | 1,117 |

### 5. FASE 1 · Variables y secuencias (2:20 – 3:00)
> "De la fecha de venta derivé las variables temporales: mes, día de la semana, semana del
> período, y las dos que pide el enunciado: `es_fin_de_semana` e `es_feriado`, con el
> calendario real de Ecuador. Agregué rezagos: ventas del día anterior, de hace siete días y
> promedio móvil de siete días. Y variables de negocio: categoría, stock y días para expirar.
> Con eso armé secuencias: una ventana de siete días por producto, con quince variables por
> paso, para predecir el día siguiente."

**Salida:** `datos/ventas_features.csv` — 600 filas × 22 columnas.

### 6. FASE 2 · Cómo modelamos (3:00 – 3:35)
> "El modelo es una red neuronal recurrente tipo LSTM, siguiendo el cuaderno de referencia:
> LSTM de 50 unidades, salida densa, pérdida MAE, optimizador Adam. Mira los últimos siete
> días y el calendario, y estima la venta del día siguiente. Se hizo finetuning por búsqueda
> de hiperparámetros, y se compara contra una línea de persistencia como baseline."

**Entradas por paso:** cantidad vendida, es_fin_de_semana, es_feriado, día (seno/coseno) y
one-hot del producto (10) = 15 variables.

### 7. FASE 2 · Resultados (3:35 – 4:30)
> "El modelo reduce el error un 45 % frente al método actual: RMSE de 24.28 unidades contra
> 44.12. El MAPE queda en 10.9 %."

| Método | RMSE | MAE | MAPE |
|---|---|---|---|
| Método actual (persistencia) | 44.12 | 32.43 | 19.54 % |
| **Modelo RNN (LSTM)** | **24.28** | **17.97** | **10.88 %** |

### 8. FASE 2 · ¿Es confiable? (4:30 – 5:10)
> "La predicción sigue la serie real, no solo el promedio. Y el método es riguroso: división
> temporal (75 % train, 25 % test), escalador ajustado solo con train, sin fuga de información.
> El test son los últimos quince días por producto."

**Rigor para el profesor:** EarlyStopping (paciencia 12), 120 épocas, batch 32, 50 unidades,
optimizador Adam, pérdida MAE.

### 9. FASE 3 · Cómo se usa (5:10 – 6:05)
> "El modelo quedó empaquetado en dos funciones: `predecir_venta(producto_id, fecha)` y
> `predecir_batch(productos, fecha)`. La segunda es la que usaría el negocio para armar el
> pedido del día."

**Ejemplo real (26 de febrero de 2022):**
| Producto | Predicción |
|---|---|
| P0001 Arroz blanco | 183.39 |
| P0005 Huevos | 259.31 |
| P0008 Agua embotellada | 291.80 |
| P0009 Galletas | 280.53 |

### 10. Impacto de negocio (6:05 – 7:05)
> "Traduzco el error a unidades: la venta media es 151 por producto y día. Un MAPE de 10.9 %
> son 16 unidades de error por producto, contra 29 del método actual. Con diez productos son
> unas 130 unidades diarias menos de error para dimensionar el pedido."

**Cifras:** 10.9 % vs 19.5 % · ~130 unidades/día menos de error (10 productos).

### 11. Roadmap y qué pedimos (7:05 – 8:15)
> "Tres pasos. Uno: piloto de cuatro a seis semanas con tus datos reales para calibrar el
> modelo. Dos: integración con el punto de venta y la reposición. Tres: monitoreo del error
> y reentrenamiento periódico.
> Lo que pedimos: aprobar el piloto y compartir el histórico de ventas.
> Honestidad: los resultados son sobre sesenta días sintéticos y ciento cincuenta predicciones
> de test. El enfoque está validado; falta calibrar con datos reales. Eso es justamente lo
> que propone el piloto."

### 12. Cierre (8:15 – 8:40)
> "El modelo ya funciona. El siguiente paso es calibrarlo con tus datos reales. Preguntas."

---

## Preguntas que te pueden hacer

**"¿Por qué no usaste el dataset de Kaggle tal cual?"**
> "Por dos razones verificadas: los 20 `Product ID` del original aparecen con las cinco
> categorías a la vez, sin catálogo consistente; y `Holiday/Promotion` no influye en
> `Units Sold` (136.5 vs 136.4). Además las fechas vienen en formato mezclado — 44,200
> filas ambiguas. Y el enunciado pedía un dataset sintético de 10 productos por 60 días,
> que es exactamente lo que construí."

**"¿No es inventarte los datos?"**
> "El dataset base es público y está en la URL; hice una transformación documentada:
> traducir, seleccionar productos reales, recortar el período y reconstruir el
> comportamiento de compra. Analizar datos aleatorios no habría permitido cumplir el
> criterio de que las figuras muestren un patrón reconocible."

**"¿Por qué `es_fin_de_semana`, `es_feriado` y `tipo_dia`? ¿No es redundante?"**
> "Son cosas distintas. Los dos indicadores son variables de modelado: binarias e
> independientes, y un día puede ser las dos cosas a la vez. `tipo_dia` es la etiqueta
> categórica para visualizar. La puse en cuatro niveles para que sea biyectiva con los dos
> indicadores: si tuviera tres, el 1 de enero —sábado y feriado— se clasificaría solo como
> 'Feriado' y se perdería que fue fin de semana."

**"¿Cómo sé que tu ingeniería de características fue buena?"**
> "Por dos vías. Técnica: la variable tiene que ser útil — sin nulos, con varianza,
> correlacionada con el target y con cobertura temporal completa; eso lo revisé en el
> control de calidad. Y de negocio: la mejora se mide contra lo que importa, que es
> cuánto stock se agota y cuánto dinero se deja de vender. Para eso hay que involucrar al
> cliente: que el dueño valide si las variables le hacen sentido, porque él sabe si el
> sábado la tienda se llena. La muestra de solo 3 días feriado es justamente el punto
> débil que revisaría con él."

**"¿Y el modelo? ¿No es muy simple?"**
> "La práctica pide un modelo RNN; usé LSTM, que es una RNN y es la arquitectura del
> cuaderno de referencia (LSTM 50 + densa, MAE, Adam). Es intencionalmente simple para un
> dataset pequeño. Con datos reales y más años de histórico se puede escalar: más variables,
> más productos, más complejidad. El pipeline ya está preparado para eso."

**"¿Por qué no usaste `fecha_expiracion`?"**
> "Está en el catálogo porque el enunciado define ese esquema, y la uso para calcular
> `dias_para_expirar`. Pero para esta tarea, que es de patrones de compra, es secundaria:
> su análisis es el de merma y vencimientos, que es otra línea de trabajo. En el reporte
> está documentada con su uso actual."

**"¿El modelo ya está listo para producción?"**
> "No. Está validado en un entorno controlado con datos sintéticos. Para producción
> necesitamos datos reales, integración con el punto de venta y monitoreo del error. Por
> eso proponemos un piloto de cuatro a seis semanas antes de escalar."

---

## Checklist antes de exponer

- [ ] `presentacion/presentacion_final.pptx` (y `.pdf`) abiertos en modo presentación.
- [ ] Las 12 diapositivas principales cargan bien; el apéndice queda oculto hasta que lo necesites.
- [ ] Tener a la mano las 5 cifras clave:
      **+55.6 %** (fin de semana) · **+40.1 %** (feriado) · **10.9 %** (MAPE LSTM) ·
      **−45 %** (reducción del error) · **~130 unidades/día** (menos error).
- [ ] Saber que el test son **15 días por producto** (150 predicciones) — si preguntan por
      el tamaño de la muestra.
- [ ] Ensayar una vez cronometrada (8:40 + margen).
- [ ] Si el profesor pregunta por el dataset: **73,100 filas**, `Holiday/Promotion` sin
      efecto, **44,200 fechas ambiguas**, `Product ID` sin categoría consistente.
- [ ] Si hay demo en vivo: preparar `predecir_batch(["P0001","P0005","P0008","P0009"],
      "2022-02-26")` con la salida ya conocida:
      P0001 183.39 · P0005 259.31 · P0008 291.80 · P0009 280.53.
