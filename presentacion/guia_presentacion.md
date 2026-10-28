# Guía de exposición — Tarea 01: Ingeniería de características

**Tiempo objetivo: 5 minutos (≈30 s por diapositiva).**
Material: `presentacion/presentacion_tarea01.pptx` (o `.pdf`).
Reporte de respaldo: `reporte/reporte_tarea01.pdf`.

---

## Cronograma

| # | Diapositiva | Tiempo | Figura |
|---|---|---|---|
| 1 | Portada | 0:00 – 0:20 | — |
| 2 | Dataset | 0:20 – 0:50 | — |
| 3 | Modificaciones al dataset | 0:50 – 1:25 | — |
| 4 | Variables creadas | 1:25 – 2:00 | — |
| 5 | Categorías más importantes | 2:00 – 2:30 | `01_ventas_por_categoria.png` |
| 6 | Ventas semana a semana | 2:30 – 3:10 | `04_semana_a_semana.png` |
| 7 | Muestreo de categorías | 3:10 – 3:35 | `06_categorias_en_tiempo.png` |
| 8 | Fin de semana vs. entre semana | 3:35 – 4:05 | `07_fin_de_semana.png` |
| 9 | Influencia de los feriados | 4:05 – 4:40 | `08_feriados.png` |
| 10 | Conclusiones | 4:40 – 5:00 | — |

> Si vas con tiempo apretado: **corta la diapositiva 7** (muestreo) y alarga la 9 (feriados).
> Si te sobra tiempo: agrega la 3 (`03_evolucion_diaria.png`) entre la 5 y la 6.

---

## Guion diapositiva por diapositiva

### 1. Portada (0:00 – 0:20)
> "Buenos días. Esta es la Tarea 01 de Ingeniería de Características: analicé un dataset de
> ventas de una tienda de retail, lo exploré, identiqué patrones de compra y construí las
> variables temporales que necesita un modelo para anticipar la demanda."

**No digas:** que el dataset es inventado de la nada. Se explica en la diapositiva 2.

---

### 2. Dataset (0:20 – 0:50) — *requisito: URL + público/construido*
> "El dataset de partida es público, de Kaggle: **Retail Store Inventory Forecasting Dataset**,
> en la URL: **kaggle.com/datasets/anirudhchauhan/retail-store-inventory-forecasting-dataset**.
> Ese dataset tiene 73 mil filas, cinco tiendas y veinte productos, pero es genérico y no permite
> un análisis de tienda.
> El dataset que yo analizo es **construido** a partir de ese: diez productos reales de una
> tienda de barrio, **sesenta días** de ventas — del 1 de enero al 1 de marzo de 2022 — que es
> justo la ventana de dos meses que pide el enunciado para el análisis semana a semana."

**Cifras que puedes citar:** 73,100 filas (original) · 10 productos × 60 días = 600 registros (construido).

---

### 3. Modificaciones al dataset (0:50 – 1:25) — *requisito: qué cambié*
> "Hice cinco cambios. El primero: traducir todo al español y reemplazar los identificadores
> genéricos por diez productos reales, cada uno con su categoría y su unidad.
> Segundo: recortar el período de dos años a sesenta días.
> Tercero, que es el más importante: el dataset original es **aleatorio** — le puedes poner un
> feriado o no y las ventas no cambian; y las fechas vienen en formato mezclado. Entonces lo
> **reconstruí** con el comportamiento real del negocio: estacionalidad semanal, impulso en
> feriados y una tendencia leve. Sin eso no había ningún patrón que analizar.
> Cuarto: separé el catálogo del historial de ventas en dos archivos. Quinto: los 20 productos
> del original no tienen categoría consistente, y los míos sí."

**Justificación clave si te la piden:** *"Lo hice porque el enunciado pide figuras con un patrón
reconocible, y el dataset original no lo tiene: `Holiday/Promotion` no influye en `Units Sold`
(136.5 vs 136.4 de promedio) y las fechas vienen en formato `m/d` y `d/m` mezclado."*

---

### 4. Variables creadas (1:25 – 2:00) — *requisito: variables + fin de semana + feriados*
> "De la fecha de venta derivé once variables: mes, día de la semana, nombre del día, semana del
> año, semana dentro del período, y las dos que pide el enunciado: **`es_fin_de_semana`**,
> un indicador que vale 1 si es sábado o domingo, y **`es_feriado`**, que vale 1 si la fecha es
> feriado nacional de Ecuador — para eso usé el calendario real: 1 de enero, 28 y 1 de febrero,
> que fue Carnaval.
> Agregué además rezagos: las ventas del día anterior, de hace siete días, y un promedio móvil
> de siete días. Y un par de variables de negocio: la categoría del producto y los días que le
> quedan para expirar."

**Detalle que da puntos:** *"`tipo_dia` la dejé en cuatro niveles —Entre semana, Fin de semana,
Feriado y Feriado (fin de semana)— porque con solo tres se perdía el 1 de enero, que es sábado
y feriado a la vez. Con cuatro niveles es biyectiva con los dos indicadores: no se pierde
información."*

---

### 5. Categorías más importantes (2:00 – 2:30) — *requisito: categorías analizadas*
> "Estas son las seis categorías. **Alimentos** concentra casi la mitad de las ventas, con el
> 49.6%. Pero fíjense que por volumen promedio por producto el orden cambia: **Bebidas** con 212
> unidades por día y **Snacks** con 199, contra Alimentos con 150. Son categorías distintas:
> Alimentos son muchas unidades al día de stock, Bebidas y Snacks son menos productos pero
>mucho más rotativos."

**Cifras por categoría (total / % / promedio diario por producto):**
| Categoría | Total | % | Prom. diario |
|---|---|---|---|
| Alimentos | 45,011 | 49.6 % | 150.0 |
| Bebidas | 12,731 | 14.0 % | 212.2 |
| Snacks | 11,968 | 13.2 % | 199.5 |
| Cuidado personal | 7,417 | 8.2 % | 123.6 |
| Hogar | 7,014 | 7.7 % | 116.9 |
| Limpieza | 6,593 | 7.3 % | 109.9 |

**Productos analizados (los 10):** Arroz blanco, Leche entera, Pan de molde, Aceite vegetal,
Huevos (Alimentos) · Detergente en polvo (Limpieza) · Jabón de baño (Cuidado personal) ·
Agua embotellada (Bebidas) · Galletas (Snacks) · Papel higiénico (Hogar).
**Más vendidos:** Agua embotellada (12,731) · Galletas (11,968) · Huevos (11,085).

---

### 6. Ventas semana a semana (2:30 – 3:10) — *requisito: semana a semana durante 2 meses*
> "Aquí está el requisito central: las compras organizadas **semana a semana** durante los dos
> meses. Son nueve paneles, uno por semana, y cada barra es el total de ese día.
> El patrón se repite: los **sábados** son los días más altos y los **miércoles** los más bajos.
> En promedio, el sábado vende 2,183 unidades y el miércoles 1,117 — casi el doble.
> Miren también el 1 de enero, la primera barra: es sábado y además Año Nuevo, y es el pico más
> alto de todo el período, 2,753 unidades."

**Cifras por día de la semana (promedio diario, toda la tienda):**

| Sábado | Domingo | Viernes | Lunes | Martes | Jueves | Miércoles |
|---|---|---|---|---|---|---|
| **2,183** | 1,851 | 1,511 | 1,347 | 1,262 | 1,241 | **1,117** |

---

### 7. Muestreo de categorías (3:10 – 3:35) — *requisito: muestreo de categorías*
> "Para facilitar la lectura tomé una muestra de tres categorías y seguí su evolución diaria.
> Se ve que cada una tiene su propio ritmo, pero las tres repiten el mismo ciclo semanal:
> suben el fin de semana y bajan entre semana. Por eso el modelo necesita las variables
> temporales: la demanda no es plana y planificarla solo con el promedio la haría fallar
> todos los fines de semana."

---

### 8. Fin de semana vs. entre semana (3:35 – 4:05)
> "Aquí cuantifico el efecto del fin de semana. El promedio diario entre semana es de 1,296
> unidades y el fin de semana sube a 2,017: **un incremento del 55.6%**.
> En el negocio esto es directo: el sábado y el domingo hay que tener más stock del habitual,
> o se pierden ventas. Por eso `es_fin_de_semana` es una variable obligatoria y no un adorno."

**Cifras:** entre semana 1,296.0 (42 días) · fin de semana 2,016.7 (18 días) · **+55.6 %**

---

### 9. Influencia de los feriados (4:05 – 4:40) — *requisito: ¿los feriados influyen?*
> "Y esta es la pregunta de fondo: **¿los feriados influyen?** En el panel izquierdo comparo
> días feriados contra días normales. El promedio en un feriado es de 2,077 unidades contra 1,482
> en un día normal: **un 40.1% más**.
> En el panel derecho están los feriados marcados sobre la serie temporal, y se ve el pico.
> Ojo con el tamaño de la muestra: solo 3 días feriado de 60, o sea el 5% del período. La
> tendencia es clara y consistente con lo que pasa en un negocio real, pero la estimación es
> preliminar; con más años de histórico se podría cuantificar mejor."

**Cifras:** feriado 2,077.3 (3 días) · no feriado 1,482.5 (57 días) · **+40.1 %**
**Feriados usados (Ecuador):** 1 ene (Año Nuevo) · 28 feb y 1 mar (Carnaval).

---

### 10. Conclusiones (4:40 – 5:00)
> "Tres conclusiones. Primero: **sí hay patrones reconocibles** — el fin de semana y los
> feriados elevan las ventas, y las figuras los muestran claramente.
> Segundo: el conocimiento del negocio fue lo que guió qué variables crear; sin saber que en
> esta tienda el flujo se concentra en fin de semana y feriados, no hubiera creado
> `es_fin_de_semana` ni `es_feriado`, y el modelo no habría aprendido a partir de ellas.
> Y tercero: las variables construidas permiten anticipar la demanda y planificar el
> inventario antes de que ocurra el pico, que es el objetivo de negocio.
> Con esto queda cerrada la entrega de la Tarea 01."

---

## Preguntas que te pueden hacer (y cómo responder)

**"¿Por qué no usaste el dataset de Kaggle tal cual?"**
> "Por dos razones concretas, y las verifiqué: primero, los 20 `Product ID` del original aparecen con las cinco categorías a la vez, o sea que no hay un catálogo consistente; segundo, el efecto de `Holiday/Promotion` es nulo (136.5 vs 136.4 unidades de promedio), y las fechas vienen con formato `m/d` y `d/m` mezclado — 44,200 filas. Además el enunciado pedía un dataset sintético de 10 productos por 60 días, que es exactamente lo que construí."

**"¿No es inventarte los datos?"**
> "El dataset base es público y está en la URL; lo que hice fue una transformación documentada: traducir, seleccionar productos reales, recortar el período y reconstruir el comportamiento de compra. Está todo detallado en la sección 1 del reporte. Y la alternativa —analizar datos aleatorios— no habría permitido cumplir el criterio de que las figuras muestren un patrón reconocible."

**"¿Por qué tienes `es_fin_de_semana`, `es_feriado` y `tipo_dia`? ¿No es redundante?"**
> "Son cosas distintas. Los dos indicadores son las variables de modelado: son binarios e independientes, y un día puede ser las dos cosas a la vez. `tipo_dia` es la etiqueta categórica para visualizar. La puse en cuatro niveles justamente para que sea biyectiva con los dos indicadores: si tuviera tres, el 1 de enero —sábado y feriado— se clasificaría solo como 'Feriado' y se perdería que fue fin de semana. Los indicadores seuls permiten reconstruir cualquier etiqueta."

**"¿Cómo sé que tu ingeniería de características fue buena?"**
> "Por dos vías. Una técnica: la variable tiene que ser útil — nulos, varianza, correlación con la variable objetivo y que la fecha cubra todo el período; eso lo revisé en el control de calidad. Y una de negocio: la mejora debe medirse contra lo que importa, que es cuánto stock se agota y cuánto dinero se deja de vender. Para eso hay que involucrar al cliente: que el dueño de la tienda valide si las variables le hacen sentido, porque él es quien sabe si el sábado la tienda se llena. La muestra de 3 días feriado es justamente el punto débil que revisaría con él."

**"¿Y el modelo?"**
> "Esta tarea es de ingeniería de características: el dataset ya queda listo con variables temporales, indicadores de fin de semana y feriado, rezagos y atributos de producto, que es exactamente lo que consume una red neuronal recurrente. Lo que sigue es la fase de modelado."

**"¿Por qué no usaste `fecha_expiracion`?"**
> "Está en el catálogo porque el enunciado define ese esquema, y la uso para calcular `dias_para_expirar`. Pero para esta tarea, que es de patrones de compra, es secundaria: su análisis es el de merma y vencimientos, que es otra línea de trabajo. En el reporte está documentada con su uso actual."

---

## Checklist antes de exponer

- [ ] `presentacion/presentacion_tarea01.pptx` (y `.pdf`) abiertos y en modo presentación.
- [ ] Las 10 figuras cargan bien (`figuras/*.png`).
- [ ] Tener a la mano: la **URL** de Kaggle y las 4 cifras clave:
      **+55.6 %** (fin de semana) · **+40.1 %** (feriado) · **49.6 %** (Alimentos) · **5 %** (días feriado).
- [ ] Tener claro que solo hay **3 días feriado** en la ventana (por eso digo "preliminar").
- [ ] Ensayar una vez cronometrada (5:00).
- [ ] Si preguntan por la justificación del dataset: **73,100 filas**, `Holiday/Promotion` sin efecto,
      **44,200 filas** con fecha ambigua, `Product ID` sin categoría consistente.
