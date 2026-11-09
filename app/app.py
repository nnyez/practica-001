"""
Servidor web mínimo con la interfaz HTML de predicción (Fase 3).

Esta carpeta (`app/`) es la capa de despliegue: no contiene lógica de negocio,
solo expone las funciones ya implementadas en `src/fase3/`.

Rutas:

* ``GET  /``              -> página con los formularios.
* ``POST /predecir``      -> ``product_id`` + ``fecha`` -> predicción individual.
* ``POST /predecir_lote`` -> lista de ``product_id`` + ``fecha`` -> predicciones.

No requiere dependencias adicionales: usa ``http.server`` de la librería
estándar y el HTML se reemplaza con ``str.replace`` (sin motor de plantillas).

Uso (desde la raíz del proyecto)::

    python -m app.app
    # -> http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

import pandas as pd

from src.fase3 import config
from src.fase3.prediccion import inicializar, predecir_batch, predecir_venta

RUTA_PLANTILLA = Path(__file__).resolve().parent / "templates" / "index.html"


# --------------------------------------------------------------------------- #
# Datos de apoyo para la interfaz
# --------------------------------------------------------------------------- #
def _datos_interfaz() -> tuple[list[tuple[str, str]], str, str]:
    """Devuelve (productos[(id, nombre)], fecha_min, fecha_max) para los formularios."""
    df = pd.read_csv(config.RUTA_DATOS, encoding="utf-8-sig", parse_dates=["fecha_venta"])
    productos = (
        df[["product_id", "nombre"]]
        .drop_duplicates()
        .sort_values("product_id")
        .itertuples(index=False, name=None)
    )
    fecha_min = (df["fecha_venta"].min() + pd.Timedelta(days=config.VENTANA)).date().isoformat()
    fecha_max = (df["fecha_venta"].max() + pd.Timedelta(days=365)).date().isoformat()
    return list(productos), fecha_min, fecha_max


PRODUCTOS, FECHA_MIN, FECHA_MAX = _datos_interfaz()
FECHA_SUGERIDA = (pd.Timestamp(FECHA_MIN) + pd.Timedelta(days=30)).date().isoformat()


# --------------------------------------------------------------------------- #
# Renderizado
# --------------------------------------------------------------------------- #
def _opciones_productos() -> str:
    return "\n".join(
        f'          <option value="{escape(pid)}">{escape(pid)} — {escape(nombre)}</option>'
        for pid, nombre in PRODUCTOS
    )


def _renderizar(resultado_html: str = "", aviso: str = "") -> bytes:
    """Carga la plantilla HTML y reemplaza los marcadores."""
    html = RUTA_PLANTILLA.read_text(encoding="utf-8")
    reemplazos = {
        "{{PRODUCTOS}}": _opciones_productos(),
        "{{RESULTADO}}": resultado_html or _bloque_vacio(),
        "{{AVISO}}": aviso,
        "{{FECHA}}": FECHA_SUGERIDA,
        "{{FECHA_MIN}}": FECHA_MIN,
        "{{FECHA_MAX}}": FECHA_MAX,
    }
    for clave, valor in reemplazos.items():
        html = html.replace(clave, valor)
    return html.encode("utf-8")


def _bloque_vacio() -> str:
    return ('<p style="color:#5a5a5a;font-size:14px;margin:6px 0;">'
            'Aún no hay predicciones. Usa uno de los formularios de arriba.</p>')


def _bloque_error(mensaje: str) -> str:
    return (f'<div class="resultado error"><div class="cifra">No se pudo calcular</div>'
            f'<div class="detalle">{escape(mensaje)}</div></div>')


def _bloque_individual(producto_id: str, fecha: str, valor: float) -> str:
    return (f'<div class="resultado">'
            f'<div class="cifra">{valor:,.0f} unidades</div>'
            f'<div class="detalle">Demanda estimada para <b>{escape(producto_id)}</b> '
            f'el <b>{escape(fecha)}</b>.</div></div>')


def _bloque_lote(fecha: str, resultados: list[dict]) -> str:
    filas = []
    ok = 0
    for r in resultados:
        if "error" in r:
            filas.append(
                f'<tr><td>{escape(str(r["producto_id"]))}</td>'
                f'<td style="color:#c62828;font-size:13px;">{escape(str(r["error"]))}</td>'
                f'<td class="num">—</td></tr>'
            )
        else:
            ok += 1
            filas.append(
                f'<tr><td>{escape(str(r["producto_id"]))}</td>'
                f'<td>predicción</td>'
                f'<td class="num">{r["prediccion"]:,.0f}</td></tr>'
            )
    total = sum(r["prediccion"] for r in resultados if "prediccion" in r)
    return (
        f'<div class="resultado"><div class="cifra">{total:,.0f} unidades</div>'
        f'<div class="detalle">{ok} de {len(resultados)} productos predichos para el '
        f'<b>{escape(fecha)}</b> (total del lote).</div></div>'
        f'<table><thead><tr><th>Producto</th><th>Estado</th>'
        f'<th style="text-align:right;">Predicción (unidades)</th></tr></thead>'
        f'<tbody>{"".join(filas)}</tbody></table>'
    )


def _parsear_productos(texto: str) -> list[str]:
    """Convierte el texto del textarea en una lista de product_id."""
    crudo = texto.replace(",", "\n").replace(";", "\n").splitlines()
    return [line.strip() for line in crudo if line.strip()]


# --------------------------------------------------------------------------- #
# Servidor
# --------------------------------------------------------------------------- #
class Handler(BaseHTTPRequestHandler):
    """Rutas HTTP de la interfaz de predicción."""

    server_version = "PrediccionDemo/1.0"

    def _responder(self, html: bytes, codigo: int = 200) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, formato: str, *args) -> None:
        print(f"[servidor] {formato % args}")

    # --- GET ---
    def do_GET(self) -> None:  # noqa: N802 (nombre impuesto por la clase base)
        if self.path in ("/", "/index.html"):
            self._responder(_renderizar())
        else:
            self._responder(b"<h1>404</h1><p>Ruta no encontrada.</p>", codigo=404)

    # --- POST ---
    def do_POST(self) -> None:  # noqa: N802
        if self.path not in ("/predecir", "/predecir_lote"):
            self._responder(b"<h1>404</h1><p>Ruta no encontrada.</p>", codigo=404)
            return

        largo = int(self.headers.get("Content-Length", 0))
        cuerpo = parse_qs(self.rfile.read(largo).decode("utf-8"))
        fecha = (cuerpo.get("fecha") or [""])[0].strip()

        if self.path == "/predecir":
            self._responder(self._predecir_individual(cuerpo, fecha))
        else:
            self._responder(self._predecir_lote(cuerpo, fecha))

    def _predecir_individual(self, cuerpo: dict, fecha: str) -> bytes:
        producto_id = (cuerpo.get("producto_id") or [""])[0].strip()
        if not producto_id or not fecha:
            return _renderizar(_bloque_error("Falta el producto o la fecha."))
        try:
            valor = predecir_venta(producto_id, fecha)
        except Exception as exc:  # noqa: BLE001 - se muestra el motivo al usuario
            return _renderizar(_bloque_error(str(exc)))
        return _renderizar(_bloque_individual(producto_id, fecha, valor))

    def _predecir_lote(self, cuerpo: dict, fecha: str) -> bytes:
        productos = _parsear_productos((cuerpo.get("productos") or [""])[0])
        if not productos or not fecha:
            return _renderizar(_bloque_error("Escribe al menos un producto y una fecha."))
        resultados = predecir_batch(productos, fecha)
        return _renderizar(_bloque_lote(fecha, resultados))


def main() -> None:
    parser = argparse.ArgumentParser(description="Interfaz web de predicción (Fase 3).")
    parser.add_argument("--host", default="127.0.0.1", help="Host de escucha (por defecto: 127.0.0.1)")
    parser.add_argument("--puerto", type=int, default=8000, help="Puerto (por defecto: 8000)")
    args = parser.parse_args()

    # Carga el modelo una vez para no repetirlo en cada petición.
    inicializar()

    servidor = HTTPServer((args.host, args.puerto), Handler)
    print("=" * 62)
    print("  Predicción de demanda — Fase 3 (interfaz web)")
    print("=" * 62)
    print(f"  Abre en el navegador:  http://{args.host}:{args.puerto}")
    print(f"  Productos disponibles: {len(PRODUCTOS)}")
    print(f"  Fechas admitidas:      {FECHA_MIN} a {FECHA_MAX}")
    print("  Ctrl+C para detener.")
    print("=" * 62)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n[servidor] detenido.")
        servidor.server_close()


if __name__ == "__main__":
    main()
