"""
Funciones para el análisis exploratorio de datos (EDA) del dataset de ventas.

Este módulo concentra las funciones reutilizables que se usan para analizar el
dataset de ventas de retail: carga y preparación, perfilado/calidad de datos,
agregaciones temporales (día de la semana, semana, fin de semana y feriados),
muestreo de categorías y generación de todas las figuras del reporte.

Cada función de gráfico devuelve el objeto ``Figure`` de matplotlib y, de forma
opcional, guarda el PNG. Todas las figuras incluyen **título** y **nombres en
los ejes X e Y**.

Uso rápido:
    from analisis_exploratorio import cargar_datos, generar_todas_las_figuras
    ventas, inventario = cargar_datos("datos")
    df = unir_inventario(ventas, inventario)
    generar_todas_las_figuras(df, "figuras")
"""

from __future__ import annotations

from pathlib import Path

import holidays
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")  # backend sin pantalla
import matplotlib.pyplot as plt
import seaborn as sns

# --------------------------------------------------------------------------- #
# Constantes
# --------------------------------------------------------------------------- #
PAIS_FERIADOS = "EC"  # Ecuador
NOMBRES_DIA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
PALETA_CATEGORICA = "viridis"
PALETA_CONTINUA = "YlGnBu"

# Columnas obligatorias de cada archivo.
COLUMNAS_VENTAS = ["product_id", "nombre", "fecha_venta", "cantidad_vendida", "stock_en_momento"]
COLUMNAS_INVENTARIO = ["product_id", "nombre", "categoria", "unidad", "stock_actual", "fecha_expiracion"]


# --------------------------------------------------------------------------- #
# Estilo
# --------------------------------------------------------------------------- #
def configurar_estilo() -> None:
    """Configura un estilo uniforme (y limpio) para todas las figuras."""
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "figure.dpi": 110,
            "savefig.dpi": 130,
            "figure.autolayout": True,
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 12,
            "font.size": 11,
        }
    )


# --------------------------------------------------------------------------- #
# Carga y preparación
# --------------------------------------------------------------------------- #
def preparar_fechas(df: pd.DataFrame, col: str = "fecha_venta") -> pd.DataFrame:
    """Convierte `col` a tipo fecha y ordena el DataFrame por esa columna."""
    df = df.copy()
    df[col] = pd.to_datetime(df[col])
    return df.sort_values(col).reset_index(drop=True)


def cargar_datos(dir_datos: str | Path = "datos") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carga `sales_history.csv` e `inventory.csv` desde `dir_datos`."""
    dir_datos = Path(dir_datos)
    ventas = pd.read_csv(dir_datos / "sales_history.csv", encoding="utf-8-sig")
    inventario = pd.read_csv(dir_datos / "inventory.csv", encoding="utf-8-sig")
    ventas = preparar_fechas(ventas, "fecha_venta")
    inventario = preparar_fechas(inventario, "fecha_expiracion")
    return ventas, inventario


def unir_inventario(ventas: pd.DataFrame, inventario: pd.DataFrame) -> pd.DataFrame:
    """Une las ventas con los atributos del producto (categoría, unidad, etc.)."""
    cols = ["product_id", "categoria", "unidad", "stock_actual", "fecha_expiracion"]
    return ventas.merge(inventario[cols], on="product_id", how="left")


def _con_categoria(df: pd.DataFrame) -> pd.DataFrame:
    """Garantiza que el DataFrame tenga la columna `categoria`."""
    if "categoria" in df.columns:
        return df
    inventario = pd.read_csv(Path(__file__).resolve().parent.parent.parent / "datos" / "inventory.csv",
                             encoding="utf-8-sig")
    return unir_inventario(df, inventario)


# --------------------------------------------------------------------------- #
# Perfilado y calidad
# --------------------------------------------------------------------------- #
def perfil_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Perfil estadístico por variable (tipo, nulos, únicos y medidas resumen)."""
    filas = []
    for col in df.columns:
        s = df[col]
        es_num = pd.api.types.is_numeric_dtype(s)
        fila = {
            "Variable": col,
            "Tipo": str(s.dtype),
            "No nulos": int(s.notna().sum()),
            "Nulos": int(s.isna().sum()),
            "Únicos": int(s.nunique(dropna=True)),
        }
        if es_num:
            fila.update(
                {
                    "Media": round(float(s.mean()), 2),
                    "Desv. estándar": round(float(s.std()), 2),
                    "Mínimo": float(s.min()),
                    "Mediana": float(s.median()),
                    "Máximo": float(s.max()),
                }
            )
        else:
            moda = s.mode(dropna=True)
            fila["Valor más común"] = f"{moda.iloc[0]} ({int((s == moda.iloc[0]).sum())})" if len(moda) else "—"
        filas.append(fila)
    return pd.DataFrame(filas)


def detectar_calidad(ventas: pd.DataFrame, inventario: pd.DataFrame) -> pd.DataFrame:
    """Reporte de calidad de datos: nulos, duplicados, cobertura y rangos."""
    hallazgos = []

    def _add(chequeo: str, resultado: str, detalle: str) -> None:
        hallazgos.append({"Chequeo": chequeo, "Resultado": resultado, "Detalle": detalle})

    faltan_v = [c for c in COLUMNAS_VENTAS if c not in ventas.columns]
    faltan_i = [c for c in COLUMNAS_INVENTARIO if c not in inventario.columns]
    _add("Columnas ventas", "OK" if not faltan_v else "FALLA",
         "Todas presentes" if not faltan_v else f"Faltan {faltan_v}")
    _add("Columnas inventario", "OK" if not faltan_i else "FALLA",
         "Todas presentes" if not faltan_i else f"Faltan {faltan_i}")

    nulos = int(ventas[COLUMNAS_VENTAS].isna().sum().sum() + inventario[COLUMNAS_INVENTARIO].isna().sum().sum())
    _add("Valores nulos", "OK" if nulos == 0 else "REVISAR", f"{nulos} celdas nulas en total")

    dup = int(ventas.duplicated(subset=["product_id", "fecha_venta"]).sum())
    _add("Duplicados (producto, fecha)", "OK" if dup == 0 else "REVISAR", f"{dup} duplicados")

    prods_ventas = set(ventas["product_id"])
    prods_inv = set(inventario["product_id"])
    _add("Productos en inventario sin ventas", "OK" if prods_inv - prods_ventas == set() else "REVISAR",
         f"{sorted(prods_inv - prods_ventas) or 'ninguno'}")

    rango = f"{ventas['fecha_venta'].min().date()} a {ventas['fecha_venta'].max().date()}"
    dias = ventas["fecha_venta"].dt.date.nunique()
    _add("Cobertura temporal", "OK" if dias >= 56 else "REVISAR", f"{dias} días ({rango})")

    neg = int((ventas["cantidad_vendida"] < 0).sum() + (ventas["stock_en_momento"] < 0).sum())
    _add("Valores negativos (ventas/stock)", "OK" if neg == 0 else "REVISAR", f"{neg} negativos")

    return pd.DataFrame(hallazgos)


def resumen_por_categoria(df: pd.DataFrame) -> pd.DataFrame:
    """Ventas totales y promedio por categoría, ordenadas de mayor a menor."""
    df = _con_categoria(df)
    res = (
        df.groupby("categoria")
        .agg(
            ventas_totales=("cantidad_vendida", "sum"),
            venta_promedio=("cantidad_vendida", "mean"),
            num_productos=("product_id", "nunique"),
        )
        .round(2)
        .sort_values("ventas_totales", ascending=False)
        .reset_index()
    )
    res["participacion_%"] = (100 * res["ventas_totales"] / res["ventas_totales"].sum()).round(1)
    return res


def resumen_por_producto(df: pd.DataFrame) -> pd.DataFrame:
    """Ventas totales y promedio por producto (más vendidos primero)."""
    res = (
        df.groupby(["product_id", "nombre"])
        .agg(
            ventas_totales=("cantidad_vendida", "sum"),
            venta_promedio=("cantidad_vendida", "mean"),
            venta_maxima=("cantidad_vendida", "max"),
        )
        .round(2)
        .sort_values("ventas_totales", ascending=False)
        .reset_index()
    )
    return res


# --------------------------------------------------------------------------- #
# Variables temporales
# --------------------------------------------------------------------------- #
def feriados_pais(fechas: pd.Series, pais: str = PAIS_FERIADOS) -> set:
    """Devuelve el conjunto de fechas que son feriado nacional en `pais`."""
    anios = sorted({int(a) for a in pd.to_datetime(fechas).dt.year.unique()})
    return set(holidays.country_holidays(pais, years=anios).keys())


def agregar_variables_temporales(df: pd.DataFrame, pais: str = PAIS_FERIADOS) -> pd.DataFrame:
    """Agrega las variables temporales base usadas en el análisis."""
    df = df.copy()
    fecha = pd.to_datetime(df["fecha_venta"])
    df["fecha_venta"] = fecha
    df["anio"] = fecha.dt.year
    df["mes"] = fecha.dt.month
    df["dia_del_mes"] = fecha.dt.day
    df["dia_semana"] = fecha.dt.weekday                       # 0=Lunes ... 6=Domingo
    df["nombre_dia"] = fecha.dt.weekday.map(dict(enumerate(NOMBRES_DIA)))
    df["es_fin_de_semana"] = (fecha.dt.weekday >= 5).astype(int)
    df["semana_iso"] = fecha.dt.isocalendar().week.astype(int)
    # Semana dentro del período analizado (1..N), para el análisis "semana a semana".
    df["semana_del_periodo"] = ((fecha - fecha.min()).dt.days // 7 + 1).astype(int)
    feriados = feriados_pais(fecha, pais)
    df["es_feriado"] = fecha.dt.date.isin(feriados).astype(int)
    return df


# --------------------------------------------------------------------------- #
# Clasificación categórica del día (fuente única de verdad)
# --------------------------------------------------------------------------- #
def etiqueta_fin_de_semana(valor: int) -> str:
    """Etiqueta legible para el indicador `es_fin_de_semana` (0/1)."""
    return "Fin de semana" if int(valor) == 1 else "Entre semana"


def etiqueta_feriado(valor: int) -> str:
    """Etiqueta legible para el indicador `es_feriado` (0/1)."""
    return "Feriado" if int(valor) == 1 else "No feriado"


def clasificar_dia(df: pd.DataFrame) -> pd.Series:
    """Etiqueta categórica de 4 niveles, biyectiva con (`es_fin_de_semana`, `es_feriado`).

    Niveles:
        - 'Entre semana'
        - 'Fin de semana'
        - 'Feriado' (entre semana)
        - 'Feriado (fin de semana)'
    """
    df = agregar_variables_temporales(df)
    return np.select(
        [(df["es_feriado"] == 1) & (df["es_fin_de_semana"] == 1),
         df["es_feriado"] == 1,
         df["es_fin_de_semana"] == 1],
        ["Feriado (fin de semana)", "Feriado", "Fin de semana"],
        default="Entre semana",
    )


# --------------------------------------------------------------------------- #
# Agregaciones temporales
# --------------------------------------------------------------------------- #
def serie_diaria(df: pd.DataFrame, por: str | None = None, agg: str = "sum") -> pd.DataFrame:
    """Serie diaria de ventas (opcionalmente agrupada por otra columna, p.ej. categoría)."""
    if por is None:
        return df.groupby("fecha_venta")["cantidad_vendida"].agg(agg).reset_index()
    tabla = df.pivot_table(index="fecha_venta", columns=por, values="cantidad_vendida", aggfunc=agg)
    return tabla.reset_index()


def agregar_por_dia_semana(df: pd.DataFrame) -> pd.DataFrame:
    """Promedio de ventas diarias por día de la semana (Lunes..Domingo)."""
    diario = df.groupby("fecha_venta")["cantidad_vendida"].sum().reset_index()
    diario["nombre_dia"] = diario["fecha_venta"].dt.weekday.map(dict(enumerate(NOMBRES_DIA)))
    res = (
        diario.groupby("nombre_dia")["cantidad_vendida"]
        .agg(venta_promedio="mean", venta_mediana="median")
        .reindex(NOMBRES_DIA)
        .round(1)
        .reset_index()
    )
    return res


def agregar_por_semana(df: pd.DataFrame) -> pd.DataFrame:
    """Ventas semanales dentro del período (semana 1..N) y su promedio diario."""
    if "semana_del_periodo" not in df:
        df = agregar_variables_temporales(df)
    total = df.groupby("semana_del_periodo")["cantidad_vendida"].sum()
    dias = df.groupby("semana_del_periodo")["fecha_venta"].nunique()
    res = pd.DataFrame({"ventas_totales": total, "dias_semana": dias}).reset_index()
    res["venta_promedio_diaria"] = (res["ventas_totales"] / res["dias_semana"]).round(1)
    return res.round(1)


def agregar_semana_dia(df: pd.DataFrame) -> pd.DataFrame:
    """Matriz semana (filas) x día de la semana (columnas) con el total vendido."""
    if "semana_del_periodo" not in df:
        df = agregar_variables_temporales(df)
    matriz = df.pivot_table(
        index="semana_del_periodo", columns="nombre_dia", values="cantidad_vendida", aggfunc="sum"
    )
    return matriz.reindex(columns=NOMBRES_DIA).fillna(0)


def comparar_fin_de_semana(df: pd.DataFrame) -> pd.DataFrame:
    """Compara el promedio diario de ventas: fin de semana vs. entre semana."""
    diario = df.groupby("fecha_venta")["cantidad_vendida"].sum().reset_index()
    diario["es_fin_de_semana"] = (diario["fecha_venta"].dt.weekday >= 5).astype(int)
    diario["tipo_dia"] = diario["es_fin_de_semana"].map(etiqueta_fin_de_semana)
    res = (
        diario.groupby("tipo_dia")["cantidad_vendida"]
        .agg(venta_promedio_diaria="mean", dias="count", ventas_totales="sum")
        .reindex(["Entre semana", "Fin de semana"])
        .round(1)
        .reset_index()
    )
    return res


def comparar_feriados(df: pd.DataFrame, pais: str = PAIS_FERIADOS) -> pd.DataFrame:
    """Compara el promedio diario de ventas: días feriados vs. días normales."""
    df = agregar_variables_temporales(df, pais)
    diario = df.groupby(["fecha_venta", "es_feriado"])["cantidad_vendida"].sum().reset_index()
    diario["feriado"] = diario["es_feriado"].map(etiqueta_feriado)
    res = (
        diario.groupby("feriado")["cantidad_vendida"]
        .agg(venta_promedio_diaria="mean", dias="count", ventas_totales="sum")
        .reindex(["No feriado", "Feriado"])
        .round(1)
        .reset_index()
    )
    return res


def listar_feriados(df: pd.DataFrame, pais: str = PAIS_FERIADOS) -> pd.DataFrame:
    """Lista los feriados presentes en el período analizado."""
    anios = sorted({int(a) for a in pd.to_datetime(df["fecha_venta"]).dt.year.unique()})
    cal = holidays.country_holidays(pais, years=anios)
    fecha = pd.to_datetime(df["fecha_venta"])
    ini, fin = fecha.min().date(), fecha.max().date()
    filas = [
        {"fecha": str(f), "dia": NOMBRES_DIA[pd.Timestamp(f).weekday()], "feriado": n}
        for f, n in sorted(cal.items())
        if ini <= f <= fin
    ]
    return pd.DataFrame(filas)


def muestrear_categorias(df: pd.DataFrame, n: int = 3, semilla: int = 42) -> list[str]:
    """Devuelve una muestra aleatoria de `n` categorías para el análisis visual."""
    df = _con_categoria(df)
    categorias = sorted(df["categoria"].unique())
    n = min(n, len(categorias))
    rng = np.random.default_rng(semilla)
    return sorted(rng.choice(categorias, size=n, replace=False).tolist())


# --------------------------------------------------------------------------- #
# Utilidades de figuras
# --------------------------------------------------------------------------- #
def guardar_figura(fig, ruta: str | Path) -> None:
    """Guarda una figura en disco creando la carpeta si no existe."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, bbox_inches="tight")
    plt.close(fig)


def _titulo_ejes(ax, titulo: str, x: str, y: str) -> None:
    ax.set_title(titulo)
    ax.set_xlabel(x)
    ax.set_ylabel(y)


# --------------------------------------------------------------------------- #
# Figuras
# --------------------------------------------------------------------------- #
def graficar_ventas_por_categoria(df, ruta=None):
    """Barras: categorías de productos más importantes (ventas totales)."""
    df = _con_categoria(df)
    res = resumen_por_categoria(df)
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=res, x="ventas_totales", y="categoria", hue="categoria",
                palette=PALETA_CATEGORICA, legend=False, ax=ax)
    for i, v in enumerate(res["ventas_totales"]):
        ax.text(v, i, f" {v:,.0f}", va="center", fontsize=10)
    _titulo_ejes(ax, "Ventas totales por categoría de producto",
                 "Ventas totales (unidades)", "Categoría")
    if ruta:
        guardar_figura(fig, ruta)
    return fig


def graficar_ventas_por_producto(df, ruta=None):
    """Barras: productos más vendidos."""
    res = resumen_por_producto(df)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=res, x="ventas_totales", y="nombre", hue="nombre",
                palette="crest", legend=False, ax=ax)
    for i, v in enumerate(res["ventas_totales"]):
        ax.text(v, i, f" {v:,.0f}", va="center", fontsize=9)
    _titulo_ejes(ax, "Ventas totales por producto",
                 "Ventas totales (unidades)", "Producto")
    if ruta:
        guardar_figura(fig, ruta)
    return fig


def graficar_evolucion_diaria(df, ruta=None):
    """Línea: evolución de las ventas diarias a lo largo del período."""
    serie = serie_diaria(df)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(serie["fecha_venta"], serie["cantidad_vendida"], marker="o", ms=3,
            color="#1f77b4", linewidth=1.5, label="Ventas diarias")
    ax.axhline(serie["cantidad_vendida"].mean(), color="gray", ls="--", lw=1,
               label="Promedio del período")
    _titulo_ejes(ax, "Evolución de las ventas diarias (enero–marzo 2022)",
                 "Fecha", "Ventas totales (unidades/día)")
    ax.legend()
    fig.autofmt_xdate()
    if ruta:
        guardar_figura(fig, ruta)
    return fig


def graficar_semana_a_semana(df, ruta=None, max_semanas: int = 9):
    """Panel semana a semana (un subplot por semana) con el total diario."""
    if "semana_del_periodo" not in df:
        df = agregar_variables_temporales(df)
    semanas = sorted(df["semana_del_periodo"].unique())[:max_semanas]
    ncols = 3
    nrows = int(np.ceil(len(semanas) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, 3.2 * nrows), sharey=True)
    axes = np.atleast_1d(axes).ravel()
    for ax, sem in zip(axes, semanas):
        sub = df[df["semana_del_periodo"] == sem]
        serie = sub.groupby("fecha_venta")["cantidad_vendida"].sum().reset_index()
        etiquetas = serie["fecha_venta"].dt.strftime("%a %d")
        ax.bar(etiquetas, serie["cantidad_vendida"], color="#2a9d8f")
        ax.set_title(f"Semana {sem}")
        ax.set_xlabel("Día")
        ax.set_ylabel("Ventas (unidades)")
        ax.tick_params(axis="x", rotation=45)
    for ax in axes[len(semanas):]:
        ax.axis("off")
    fig.suptitle("Comportamiento de las compras semana a semana", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    if ruta:
        guardar_figura(fig, ruta)
    return fig


def graficar_heatmap_semana_dia(df, ruta=None):
    """Heatmap: intensidad de ventas por semana y día de la semana."""
    matriz = agregar_semana_dia(df)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(matriz, annot=True, fmt=".0f", cmap=PALETA_CONTINUA, ax=ax,
                cbar_kws={"label": "Ventas (unidades)"})
    _titulo_ejes(ax, "Ventas por semana y día de la semana",
                 "Día de la semana", "Semana del período")
    if ruta:
        guardar_figura(fig, ruta)
    return fig


def graficar_categorias_en_tiempo(df, categorias=None, ruta=None, n: int = 3):
    """Líneas: evolución de las ventas del muestreo de categorías."""
    df = _con_categoria(df)
    if categorias is None:
        categorias = muestrear_categorias(df, n=n)
    sub = df[df["categoria"].isin(categorias)]
    serie = sub.pivot_table(index="fecha_venta", columns="categoria",
                            values="cantidad_vendida", aggfunc="sum")
    fig, ax = plt.subplots(figsize=(12, 5))
    serie.plot(ax=ax, linewidth=1.5)
    _titulo_ejes(ax, f"Muestreo de categorías: ventas diarias ({', '.join(categorias)})",
                 "Fecha", "Ventas (unidades/día)")
    ax.legend(title="Categoría")
    fig.autofmt_xdate()
    if ruta:
        guardar_figura(fig, ruta)
    return fig


def graficar_fin_de_semana(df, ruta=None):
    """Barras + comparación: fin de semana vs. entre semana."""
    res = comparar_fin_de_semana(df)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=res, x="tipo_dia", y="venta_promedio_diaria", hue="tipo_dia",
                palette=["#457b9d", "#e76f51"], legend=False, ax=ax)
    for i, v in enumerate(res["venta_promedio_diaria"]):
        ax.text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=11)
    _titulo_ejes(ax, "Promedio diario de ventas: fin de semana vs. entre semana",
                 "Tipo de día", "Venta promedio diaria (unidades)")
    if ruta:
        guardar_figura(fig, ruta)
    return fig


def graficar_feriados(df, ruta=None, pais: str = PAIS_FERIADOS):
    """Figura doble: comparación feriado/no feriado y serie con feriados marcados."""
    df = agregar_variables_temporales(df, pais)
    res = comparar_feriados(df, pais)
    serie = df.groupby(["fecha_venta", "es_feriado"])["cantidad_vendida"].sum().reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    sns.barplot(data=res, x="feriado", y="venta_promedio_diaria", hue="feriado",
                palette=["#8d99ae", "#e63946"], legend=False, ax=axes[0])
    for i, v in enumerate(res["venta_promedio_diaria"]):
        axes[0].text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=11)
    _titulo_ejes(axes[0], "Promedio diario: feriados vs. no feriados",
                 "Día", "Venta promedio diaria (unidades)")

    axes[1].plot(serie["fecha_venta"], serie["cantidad_vendida"], color="#457b9d",
                 linewidth=1.3, marker="o", ms=3, label="Ventas diarias")
    feriados = serie[serie["es_feriado"] == 1]
    axes[1].scatter(feriados["fecha_venta"], feriados["cantidad_vendida"], color="#e63946",
                    s=90, zorder=5, label="Feriado")
    _titulo_ejes(axes[1], "Ventas diarias y días feriados",
                 "Fecha", "Ventas totales (unidades/día)")
    axes[1].legend()
    axes[1].tick_params(axis="x", rotation=45)
    fig.suptitle("Influencia de los feriados en las compras", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    if ruta:
        guardar_figura(fig, ruta)
    return fig


def graficar_distribuciones(df, ruta=None):
    """Histogramas: distribución de la cantidad vendida y del stock."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    sns.histplot(df["cantidad_vendida"], bins=25, kde=True, color="#2a9d8f", ax=axes[0])
    _titulo_ejes(axes[0], "Distribución de la cantidad vendida",
                 "Cantidad vendida (unidades)", "Frecuencia")
    sns.histplot(df["stock_en_momento"], bins=25, kde=True, color="#e9c46a", ax=axes[1])
    _titulo_ejes(axes[1], "Distribución del stock en el momento de la venta",
                 "Stock en el momento (unidades)", "Frecuencia")
    fig.suptitle("Distribuciones de las variables numéricas", fontsize=15, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    if ruta:
        guardar_figura(fig, ruta)
    return fig


def graficar_stock_vs_ventas(df, ruta=None):
    """Dispersión: relación entre el stock disponible y las ventas."""
    df = _con_categoria(df)
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.scatterplot(data=df, x="stock_en_momento", y="cantidad_vendida",
                    hue="categoria", alpha=0.65, ax=ax)
    corr = df["stock_en_momento"].corr(df["cantidad_vendida"])
    _titulo_ejes(ax, "Relación entre el stock disponible y las ventas",
                 "Stock en el momento (unidades)", "Cantidad vendida (unidades)")
    ax.text(0.02, 0.98, f"Correlación = {corr:.2f}", transform=ax.transAxes,
            va="top", fontsize=11, bbox=dict(boxstyle="round", fc="white", ec="gray"))
    ax.legend(title="Categoría", bbox_to_anchor=(1.02, 1), loc="upper left")
    if ruta:
        guardar_figura(fig, ruta)
    return fig


def graficar_tres_categorias_por_semana(df, categorias=None, ruta=None, top_n: int = 3):
    """Figura única: tendencia e histórico semanal de 3 categorías + fluctuación por semana.

    Muestra las ventas totales semanales por categoría para las 3 más representativas,
    permitiendo observar su evolución histórica y la fluctuación entre semanas.
    """
    df = _con_categoria(df)
    if categorias is None:
        tot_cat = df.groupby("categoria")["cantidad_vendida"].sum().sort_values(ascending=False)
        categorias = tot_cat.head(top_n).index.tolist()

    df = agregar_variables_temporales(df)
    tmp = df[df["categoria"].isin(categorias)].copy()
    semanal = (
        tmp.groupby(["semana_del_periodo", "categoria"])["cantidad_vendida"]
        .sum()
        .reset_index()
        .sort_values(["semana_del_periodo", "categoria"])
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=semanal, x="semana_del_periodo", y="cantidad_vendida", hue="categoria",
                palette="Set2", ax=ax)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    _titulo_ejes(
        ax,
        f"Ventas totales por semana - {', '.join(categorias)} (tendencia e histórico)",
        "Semana del periodo (1 - 9)",
        "Ventas totales semanales (unidades)",
    )
    ax.legend(title="Categoría", loc="upper right")
    for c in ax.containers:
        ax.bar_label(c, fmt="%d", padding=2, fontsize=8)
    if ruta:
        guardar_figura(fig, ruta)
    return fig


# --------------------------------------------------------------------------- #
# Orquestador
# --------------------------------------------------------------------------- #
def generar_todas_las_figuras(df: pd.DataFrame, dir_salida: str | Path = "figuras",
                              pais: str = PAIS_FERIADOS) -> list[Path]:
    """Genera y guarda todas las figuras del análisis exploratorio."""
    configurar_estilo()
    dir_salida = Path(dir_salida)
    df = agregar_variables_temporales(df, pais)

    tareas = [
        ("01_ventas_por_categoria.png", lambda r: graficar_ventas_por_categoria(df, r)),
        ("02_ventas_por_producto.png", lambda r: graficar_ventas_por_producto(df, r)),
        ("03_evolucion_diaria.png", lambda r: graficar_evolucion_diaria(df, r)),
        ("04_semana_a_semana.png", lambda r: graficar_semana_a_semana(df, r)),
        ("05_heatmap_semana_dia.png", lambda r: graficar_heatmap_semana_dia(df, r)),
        ("06_categorias_en_tiempo.png", lambda r: graficar_categorias_en_tiempo(df, ruta=r, n=3)),
        ("07_fin_de_semana.png", lambda r: graficar_fin_de_semana(df, r)),
        ("08_feriados.png", lambda r: graficar_feriados(df, r, pais)),
        ("09_distribuciones.png", lambda r: graficar_distribuciones(df, r)),
        ("10_stock_vs_ventas.png", lambda r: graficar_stock_vs_ventas(df, r)),
        ("11_tres_categorias_por_semana.png", lambda r: graficar_tres_categorias_por_semana(df, ruta=r, top_n=3)),
    ]

    rutas: list[Path] = []
    for nombre, fn in tareas:
        ruta = dir_salida / nombre
        fn(ruta)
        rutas.append(ruta)
        print(f"[figura] {ruta}")
    return rutas


def main() -> None:
    """Ejecuta el EDA completo: carga datos, perfila y genera las figuras."""
    base = Path(__file__).resolve().parent.parent.parent
    ventas, inventario = cargar_datos(base / "datos")
    df = unir_inventario(ventas, inventario)

    print("=== Perfil de ventas ===")
    print(perfil_dataset(ventas).to_string(index=False))
    print("\n=== Calidad de datos ===")
    print(detectar_calidad(ventas, inventario).to_string(index=False))
    print("\n=== Resumen por categoría ===")
    print(resumen_por_categoria(df).to_string(index=False))
    print("\n=== Fin de semana vs entre semana ===")
    print(comparar_fin_de_semana(df).to_string(index=False))
    print("\n=== Feriados vs no feriados ===")
    print(comparar_feriados(df).to_string(index=False))

    generar_todas_las_figuras(df, base / "figuras")


if __name__ == "__main__":
    main()
