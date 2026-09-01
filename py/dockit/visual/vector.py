"""Adaptador SVG determinista para visuales informativas y normativas.

Los modelos raster no son tipógrafos. Este adaptador conserva títulos,
números de ley, etiquetas y procedencia como texto SVG real, seleccionable y
auditable. La salida sigue siendo vectorial y puede editarse antes de insertarla.
"""

from __future__ import annotations

import html
import re
import textwrap
from pathlib import Path

from .dominio import PlanVisual, Visual


W, H = 1600, 900
PALETAS = {
    "tinta": {
        "fondo": "#FFFFFF", "tinta": "#182126", "suave": "#5B6970",
        "primario": "#0B6B61", "secundario": "#DCEDE9", "acento": "#F3B33D",
        "papel": "#F6F8F8",
    },
    "institucional": {
        "fondo": "#F7F7F2", "tinta": "#263019", "suave": "#66705A",
        "primario": "#455119", "secundario": "#E4E6D5", "acento": "#C9A538",
        "papel": "#FFFFFF",
    },
}


def _e(texto: str) -> str:
    return html.escape(str(texto), quote=True)


def _lineas(texto: str, ancho: int, maximo: int | None = None) -> list[str]:
    lineas = textwrap.wrap(
        " ".join((texto or "").split()), width=ancho,
        break_long_words=False, break_on_hyphens=False,
    ) or [""]
    if maximo and len(lineas) > maximo:
        lineas = lineas[:maximo]
        lineas[-1] = lineas[-1].rstrip(" .") + "…"
    return lineas


def _texto(
    lineas: list[str], x: int, y: int, *, tam: int, color: str,
    peso: int = 400, interlinea: float = 1.18, ancla: str = "start",
) -> str:
    spans = []
    for i, linea in enumerate(lineas):
        dy = 0 if i == 0 else int(tam * interlinea)
        spans.append(f'<tspan x="{x}" dy="{dy}">{_e(linea)}</tspan>')
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, sans-serif" '
        f'font-size="{tam}" font-weight="{peso}" text-anchor="{ancla}">'
        + "".join(spans) + "</text>"
    )


def _cabecera(v: Visual, c: dict[str, str]) -> str:
    titulo = _texto(_lineas(v.titulo, 42, 2), 92, 104, tam=50, color=c["tinta"], peso=700)
    etiqueta = _texto(
        [v.tipo.upper()], 1510, 82, tam=20, color=c["primario"], peso=700, ancla="end"
    )
    return titulo + etiqueta


def _pie(v: Visual, c: dict[str, str]) -> str:
    ref = v.procedencia.referencia or v.procedencia.url
    if not ref and v.motor in {"sdxl", "imagegen"}:
        ref = f"Generada con {v.motor}; conservar modelo, prompt y semilla en el manifiesto."
    if not ref:
        return ""
    return _texto(
        _lineas(f"Fuente: {ref}", 125, 1), 92, 856,
        tam=18, color=c["suave"], peso=400,
    )


def _tarjeta(x: int, y: int, w: int, h: int, c: dict[str, str], activa: bool = False) -> str:
    relleno = c["secundario"] if activa else c["papel"]
    borde = c["primario"] if activa else "#CCD5D7"
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="28" '
        f'fill="{relleno}" stroke="{borde}" stroke-width="3"/>'
    )


def _legal(v: Visual, c: dict[str, str]) -> str:
    visibles = list(v.texto_visible) or [v.titulo]
    principal = visibles[0]
    secundarios = visibles[1:] or list(v.conceptos[:3])
    s = _tarjeta(92, 205, 1416, 535, c, activa=True)
    # Documento abierto: forma reconocible, pero el contenido nunca queda
    # reducido al icono. El nombre real domina la composición.
    s += (
        f'<path d="M210 304 Q410 250 650 310 V650 Q420 600 210 650 Z" '
        f'fill="{c["papel"]}" stroke="{c["primario"]}" stroke-width="5"/>'
        f'<path d="M650 310 Q890 250 1090 304 V650 Q880 600 650 650 Z" '
        f'fill="{c["papel"]}" stroke="{c["primario"]}" stroke-width="5"/>'
        f'<path d="M650 310 V650" stroke="{c["acento"]}" stroke-width="8"/>'
    )
    s += _texto(_lineas(principal, 26, 3), 650, 385, tam=45, color=c["tinta"], peso=700, ancla="middle")
    y = 510
    for item in secundarios[:3]:
        s += f'<circle cx="440" cy="{y - 12}" r="10" fill="{c["acento"]}"/>'
        s += _texto(_lineas(item, 48, 2), 470, y, tam=25, color=c["tinta"], peso=400)
        y += 72
    if v.procedencia.verificada:
        s += (
            f'<circle cx="1325" cy="315" r="66" fill="{c["primario"]}"/>'
            f'<path d="M1292 315 L1318 341 L1362 290" fill="none" '
            f'stroke="#FFFFFF" stroke-width="15" stroke-linecap="round" '
            f'stroke-linejoin="round"/>'
        )
        s += _texto(["FUENTE", "VERIFICADA"], 1325, 405, tam=17, color=c["primario"], peso=700, ancla="middle")
    return s


def _proceso(v: Visual, c: dict[str, str]) -> str:
    items = list(v.texto_visible or v.conceptos)
    if not items:
        items = [v.proposito]
    items = items[:5]
    margen, hueco = 92, 28
    ancho = int((W - 2 * margen - hueco * (len(items) - 1)) / max(1, len(items)))
    s = ""
    for i, item in enumerate(items):
        x = margen + i * (ancho + hueco)
        s += _tarjeta(x, 280, ancho, 330, c, activa=i == len(items) - 1)
        s += f'<circle cx="{x + ancho // 2}" cy="350" r="38" fill="{c["primario"]}"/>'
        s += _texto([str(i + 1)], x + ancho // 2, 364, tam=31, color="#FFFFFF", peso=700, ancla="middle")
        s += _texto(_lineas(item, max(13, ancho // 18), 5), x + ancho // 2, 445, tam=25, color=c["tinta"], peso=600, ancla="middle")
        if i < len(items) - 1:
            x1, x2, y = x + ancho + 5, x + ancho + hueco - 5, 445
            s += f'<path d="M{x1} {y} H{x2}" stroke="{c["acento"]}" stroke-width="8"/>'
            s += f'<path d="M{x2 - 16} {y - 13} L{x2} {y} L{x2 - 16} {y + 13}" fill="none" stroke="{c["acento"]}" stroke-width="8"/>'
    return s


def _comparacion(v: Visual, c: dict[str, str]) -> str:
    items = list(v.texto_visible or v.conceptos)
    mitad = max(1, (len(items) + 1) // 2)
    lados = (items[:mitad], items[mitad:] or [v.proposito])
    s = ""
    for lado, grupo in enumerate(lados):
        x = 92 + lado * 730
        s += _tarjeta(x, 235, 686, 480, c, activa=lado == 1)
        rotulo = "A" if lado == 0 else "B"
        s += _texto([rotulo], x + 48, 300, tam=30, color=c["primario"], peso=700)
        y = 370
        for item in grupo[:4]:
            s += f'<circle cx="{x + 56}" cy="{y - 9}" r="8" fill="{c["acento"]}"/>'
            s += _texto(_lineas(item, 37, 2), x + 82, y, tam=25, color=c["tinta"], peso=500)
            y += 82
    return s


def _generico(v: Visual, c: dict[str, str]) -> str:
    items = list(v.texto_visible or v.conceptos)
    if not items:
        items = [v.proposito]
    items = items[:6]
    columnas = 3 if len(items) > 2 else max(1, len(items))
    filas = (len(items) + columnas - 1) // columnas
    ancho, alto = 430, 205
    total_w = columnas * ancho + (columnas - 1) * 36
    x0 = (W - total_w) // 2
    y0 = 240 if filas > 1 else 310
    s = ""
    for i, item in enumerate(items):
        col, fila = i % columnas, i // columnas
        x, y = x0 + col * (ancho + 36), y0 + fila * (alto + 34)
        s += _tarjeta(x, y, ancho, alto, c, activa=i == 0)
        s += f'<circle cx="{x + 58}" cy="{y + 58}" r="26" fill="{c["acento"]}"/>'
        s += _texto([str(i + 1)], x + 58, y + 69, tam=24, color=c["tinta"], peso=700, ancla="middle")
        s += _texto(_lineas(item, 28, 4), x + 104, y + 60, tam=24, color=c["tinta"], peso=600)
    return s


def generar_svg(v: Visual, paleta: str = "tinta") -> str:
    c = PALETAS.get(paleta, PALETAS["tinta"])
    if v.tipo == "ley" or v.es_normativa:
        cuerpo = _legal(v, c)
    elif v.tipo == "proceso":
        cuerpo = _proceso(v, c)
    elif v.tipo == "comparacion":
        cuerpo = _comparacion(v, c)
    else:
        cuerpo = _generico(v, c)
    desc = v.texto_alternativo or v.proposito
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-labelledby="titulo desc">'
        f'<title id="titulo">{_e(v.titulo)}</title><desc id="desc">{_e(desc)}</desc>'
        f'<rect width="{W}" height="{H}" fill="{c["fondo"]}"/>'
        f'{_cabecera(v, c)}{cuerpo}{_pie(v, c)}</svg>'
    )


def nombre_archivo(v: Visual) -> str:
    seguro = re.sub(r"[^a-z0-9]+", "-", v.tipo.lower()).strip("-") or "visual"
    return f"diapo{v.diapositiva:02d}_op{v.opcion}_{seguro}.svg"


def generar_plan(
    plan: PlanVisual,
    destino: str | Path,
    *,
    paleta: str = "tinta",
    sobrescribir: bool = False,
) -> list[Path]:
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    creados: list[Path] = []
    for v in plan.visuales:
        if v.motor not in {"vector", "nativo"} or v.tipo in {"portada", "ninguno"}:
            continue
        ruta = destino / nombre_archivo(v)
        if ruta.exists() and not sobrescribir:
            raise FileExistsError(f"{ruta} ya existe; usa --sobrescribir")
        ruta.write_text(generar_svg(v, paleta), encoding="utf-8")
        creados.append(ruta)
    return creados
