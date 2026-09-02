# -*- coding: utf-8 -*-
"""Arquetipos de diagrama conceptual para las diapositivas del examen de ascenso.

Resuelve localmente el registro C del método (`analisis/metodo_semantico.md`): la opción
conceptual de cada diapositiva se declara en una línea de JSON y se dibuja como SVG
determinista, sin modelo generativo, sin texto y en la paleta de la plantilla.

    {"tipo": "fila", "iconos": ["ojo", "candado", "farola"], "acento": [0]}

Reutiliza la biblioteca de iconos canónica de `pptx_/vector.py`.

**Los diagramas dibujan sus rótulos.** Antes no lo hacían —se dejaba la franja
inferior libre para que el usuario los escribiera a mano en PowerPoint— y el
resultado fueron láminas de iconos sin una sola letra, imposibles de relacionar
con lo que decía la diapositiva. Un diagrama sin rótulos no es un diagrama: es
un adorno.
"""

from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# La biblioteca de iconos vive en el paquete pptx_. Antes se apuntaba a la
# carpeta del proyecto original, que dejó de existir al centralizar el código.
CANONICO = Path(__file__).resolve().parent.parent / "pptx_" / "vector.py"

# Paleta por defecto: la de la plantilla del proyecto policial, que es de
# donde vienen estos arquetipos. Cualquier trabajo puede imponer la suya con
# spec["paleta"], y debe hacerlo: un diagrama con colores ajenos a la
# diapositiva parece pegado de otra presentación.
OLIVA, VERDE, GRIS, ORO = "#455119", "#5E672C", "#838858", "#C9A538"
FONDO, PAPEL, TENUE = "#F4F2EA", "#EDEADE", "#B9BCA4"

_ACTIVA: dict[str, str] = {}


def _c(valor: str) -> str:
    """Normaliza un color a #RRGGBB."""
    v = str(valor).strip().lstrip("#")
    return f"#{v.upper()}" if len(v) == 6 else valor


def aplicar_paleta(paleta: dict | None) -> None:
    """Fija la paleta de este dibujo. Sin argumento, vuelve a la de siempre.

    Se mapea desde los nombres que usa la lámina (primary/accent/ink/soft) a
    los papeles del diagrama, para que no haya que traducir en cada llamada.
    """
    global OLIVA, VERDE, GRIS, ORO, FONDO, PAPEL, TENUE, _ACTIVA
    if not paleta:
        OLIVA, VERDE, GRIS, ORO = "#455119", "#5E672C", "#838858", "#C9A538"
        FONDO, PAPEL, TENUE = "#F4F2EA", "#EDEADE", "#B9BCA4"
        _ACTIVA = {}
        return
    OLIVA = _c(paleta.get("primary", "#455119"))
    ORO = _c(paleta.get("accent", "#C9A538"))
    VERDE = _c(paleta.get("ink", OLIVA))
    GRIS = _c(paleta.get("muted", "#838858"))
    FONDO = _c(paleta.get("pale", paleta.get("paper", "#FFFFFF")))
    PAPEL = _c(paleta.get("soft", FONDO))
    TENUE = _c(paleta.get("muted", "#B9BCA4"))
    _ACTIVA = dict(paleta)


def _cargar_iconos() -> dict:
    spec = importlib.util.spec_from_file_location("vector_canonico", CANONICO)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no se encuentra la biblioteca de iconos en {CANONICO}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vector_canonico"] = mod
    spec.loader.exec_module(mod)
    return mod.ICONS


ICONS = _cargar_iconos()


def icono(nombre: str, cx: float, cy: float, s: float, c: str = OLIVA, a: str = ORO) -> str:
    """Coloca un icono de la biblioteca (viewBox 100x100) centrado en (cx, cy) con lado s."""
    if nombre not in ICONS:
        raise KeyError(f"icono desconocido: {nombre}. Disponibles: {sorted(ICONS)}")
    cuerpo = ICONS[nombre].format(c=c, a=a)
    k = s / 100.0
    return f'<g transform="translate({cx - s / 2:.1f},{cy - s / 2:.1f}) scale({k:.4f})">{cuerpo}</g>'


def _colores(activo: bool) -> tuple[str, str]:
    """Un elemento acentuado lleva el oro; el resto queda en oliva sobre gris."""
    return (OLIVA, ORO) if activo else (GRIS, TENUE)


def _marco(w: int, h: int, cuerpo: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
        f'<rect width="{w}" height="{h}" fill="{FONDO}"/>{cuerpo}</svg>'
    )


TIPO_LETRA = "DejaVu Sans, Liberation Sans, Arial, sans-serif"
ROTULO_PX, TITULO_PX = 34, 46
MAX_LINEAS = 3


def _escapar(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _partir(texto: str, max_car: int) -> list[str]:
    """Parte el rótulo en líneas por palabras; si no cabe, lo recorta con puntos
    suspensivos en vez de dejar que se salga del lienzo."""
    palabras = str(texto).split()
    lineas, actual = [], ""
    for palabra in palabras:
        prueba = f"{actual} {palabra}".strip()
        if len(prueba) <= max_car:
            actual = prueba
            continue
        if actual:
            lineas.append(actual)
        actual = palabra
        if len(lineas) == MAX_LINEAS:
            break
    if actual and len(lineas) < MAX_LINEAS:
        lineas.append(actual)
    if not lineas:
        return [""]
    if len(lineas) == MAX_LINEAS and len(" ".join(palabras)) > sum(map(len, lineas)) + 2:
        lineas[-1] = lineas[-1][:max_car - 1].rstrip() + "…"
    return lineas


def texto(x: float, y: float, contenido: str, px: int = ROTULO_PX,
          color: str = OLIVA, peso: str = "600", ancla: str = "middle",
          max_car: int = 22) -> str:
    """Un rótulo centrado, partido en líneas si hace falta."""
    lineas = _partir(contenido, max_car)
    salida = (f'<text x="{x:.0f}" y="{y:.0f}" font-family="{TIPO_LETRA}" '
              f'font-size="{px}" font-weight="{peso}" fill="{color}" '
              f'text-anchor="{ancla}">')
    for i, linea in enumerate(lineas):
        dy = 0 if i == 0 else px * 1.15
        salida += (f'<tspan x="{x:.0f}" dy="{dy:.0f}">{_escapar(linea)}</tspan>')
    return salida + "</text>"


# Marca invisible que deja el arquetipo que ya rotuló. Comprobarlo mirando el
# texto no vale: los rótulos van partidos en <tspan> y nunca coinciden enteros.
MARCA_ROTULOS = "<!--rotulos-->"


def _rotulos_de(spec: dict) -> list[str]:
    return [str(r) for r in (spec.get("rotulos") or spec.get("etiquetas") or [])]


def _banda_rotulos(spec: dict, w: int, h: int, posiciones: list[float],
                   y: float) -> str:
    """Rótulos alineados bajo cada elemento del diagrama."""
    rotulos = _rotulos_de(spec)
    if not rotulos or not posiciones:
        return ""
    n = max(len(posiciones), 1)
    ancho = w / n
    # con muchas columnas el rótulo encoge un poco y se parte en más líneas,
    # que es preferible a que dos rótulos vecinos se toquen
    px = ROTULO_PX if n <= 3 else max(24, int(ROTULO_PX * 0.78))
    max_car = max(10, int(ancho * 0.92 / (px * 0.55)))
    acento = set(spec.get("acento", range(len(rotulos))))
    salida = MARCA_ROTULOS
    for i, x in enumerate(posiciones):
        if i >= len(rotulos):
            break
        salida += texto(x, y, rotulos[i], px,
                        OLIVA if i in acento else GRIS, max_car=max_car)
    return salida


def _titulo(spec: dict, w: int) -> str:
    titulo = str(spec.get("titulo") or "").strip()
    if not titulo:
        return ""
    return texto(w / 2, 74, titulo, TITULO_PX, OLIVA, "700",
                 max_car=max(18, int(w / (TITULO_PX * 0.52))))


# --------------------------------------------------------------------------- arquetipos

def triangulo(spec, w, h):
    """Tres elementos que deben converger; el centro compartido va en oro."""
    ic = spec["iconos"][:3]
    cx, r = w / 2, min(w, h) * 0.36
    pts = [(cx, h * 0.20), (cx + r * 1.02, h * 0.86), (cx - r * 1.02, h * 0.86)]
    s = f'<polygon points="{" ".join(f"{x:.0f},{y:.0f}" for x, y in pts)}" fill="none" stroke="{OLIVA}" stroke-width="7" opacity=".85"/>'
    gx, gy = cx, sum(p[1] for p in pts) / 3
    d = min(w, h) * 0.15
    s += f'<polygon points="{gx:.0f},{gy - d:.0f} {gx + d * 0.95:.0f},{gy + d * 0.62:.0f} {gx - d * 0.95:.0f},{gy + d * 0.62:.0f}" fill="{ORO}" opacity=".95"/>'
    rad = min(w, h) * 0.115
    for i, (x, y) in enumerate(pts):
        ausente = i in spec.get("ausente", [])
        dash = ' stroke-dasharray="18 14"' if ausente else ""
        s += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rad:.0f}" fill="{PAPEL}" stroke="{OLIVA}" stroke-width="7"{dash}/>'
        c, a = (GRIS, TENUE) if ausente else (OLIVA, ORO)
        s += icono(ic[i], x, y, rad * 1.15, c, a)
    return s


def fila(spec, w, h):
    """N elementos enumerados en una fila; el oro marca los que la diapositiva destaca."""
    ic = spec["iconos"]
    n = len(ic)
    acento = set(spec.get("acento", range(n)))
    banda = h * 0.16  # franja inferior limpia para los rótulos
    cy = (h - banda) / 2
    paso = w / n
    rad = min(paso * 0.34, (h - banda) * 0.33)
    s = ""
    for i, nombre in enumerate(ic):
        x = paso * (i + 0.5)
        activo = i in acento
        c, a = _colores(activo)
        borde = OLIVA if activo else GRIS
        s += f'<circle cx="{x:.0f}" cy="{cy:.0f}" r="{rad:.0f}" fill="{PAPEL}" stroke="{borde}" stroke-width="6"/>'
        s += icono(nombre, x, cy, rad * 1.2, c, a)
    # la franja inferior era para los rótulos y estaba vacía: aquí se dibujan
    s += _banda_rotulos(spec, w, h, [paso * (i + 0.5) for i in range(n)],
                        cy + rad + ROTULO_PX * 1.5)
    return s


def capas(spec, w, h):
    """Capas concéntricas de protección alrededor de un bien: más capas, menos rentable."""
    ic = spec["iconos"]
    n = len(ic)
    cx, cy = w / 2, h / 2
    base = min(w, h) * 0.42
    s = ""
    for i in range(n, 0, -1):
        r = base * (0.32 + 0.23 * i)
        color = ORO if i == n else OLIVA
        s += (f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="none" stroke="{color}" '
              f'stroke-width="{5 + i * 3}" opacity="{0.45 + 0.14 * i:.2f}"/>')
    for i, nombre in enumerate(ic):
        r = base * (0.32 + 0.23 * (i + 1))
        ang = math.radians(-90 + i * (360 / n))   # repartidos alrededor, no apiñados arriba
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
        s += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{base * 0.20:.0f}" fill="{FONDO}"/>'
        s += icono(nombre, x, y, base * 0.30, OLIVA, ORO)
    if spec.get("nucleo"):
        s += icono(spec["nucleo"], cx, cy, base * 0.40, OLIVA, ORO)
    return s

def embudo(spec, w, h):
    """De muchos casos a uno seleccionado, y de ahí a las medidas que se eligen."""
    ic = spec.get("iconos", [])
    cx = w / 2
    for_y = h * 0.10
    s = ""
    for i in range(22):  # dispersión inicial
        x = cx + (i % 11 - 5) * w * 0.062
        y = for_y + (i // 11) * h * 0.062
        s += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="9" fill="{GRIS}" opacity=".55"/>'
    s += (f'<polygon points="{cx - w * 0.30:.0f},{h * 0.28:.0f} {cx + w * 0.30:.0f},{h * 0.28:.0f} '
          f'{cx + w * 0.05:.0f},{h * 0.56:.0f} {cx - w * 0.05:.0f},{h * 0.56:.0f}" fill="{OLIVA}" opacity=".16" '
          f'stroke="{OLIVA}" stroke-width="5"/>')
    s += f'<circle cx="{cx:.0f}" cy="{h * 0.62:.0f}" r="20" fill="{ORO}"/>'
    if ic:
        paso = w / (len(ic) + 1)
        for i, nombre in enumerate(ic):
            x = paso * (i + 1)
            s += (f'<path d="M {cx:.0f} {h * 0.64:.0f} C {cx:.0f} {h * 0.76:.0f}, {x:.0f} {h * 0.72:.0f}, '
                  f'{x:.0f} {h * 0.80:.0f}" fill="none" stroke="{OLIVA}" stroke-width="5" opacity=".6"/>')
            s += icono(nombre, x, h * 0.88, min(paso * 0.55, h * 0.17), OLIVA, ORO)
    return s


def contraste(spec, w, h):
    """Dos mitades enfrentadas: antes y después, o dos vías de acción."""
    izq, der = spec["izquierda"], spec["derecha"]
    alto = h * 0.85          # el resto queda como franja limpia para los rótulos
    cy = alto * 0.52
    acento = spec.get("acento", "derecha")
    s = ""
    for lado, iconos, activo in ((0, izq, acento == "izquierda"), (1, der, acento == "derecha")):
        x0 = w * (0.04 + 0.48 * lado)
        relleno = PAPEL if activo else "#E7E5DA"
        borde = OLIVA if activo else GRIS
        guion = "" if activo else ' stroke-dasharray="16 12"'
        s += (f'<rect x="{x0:.0f}" y="{alto * 0.10:.0f}" width="{w * 0.44:.0f}" '
              f'height="{alto * 0.80:.0f}" rx="22" fill="{relleno}" stroke="{borde}" '
              f'stroke-width="6"{guion}/>')
        c, a = _colores(activo)
        n = max(len(iconos), 1)
        paso = (w * 0.44) / n
        tam = min(paso * 0.80, alto * 0.44)
        for i, nombre in enumerate(iconos):
            s += icono(nombre, x0 + paso * (i + 0.5), cy, tam, c, a)
    return s

def escalera(spec, w, h):
    """Escalamiento por peldaños y el corte preventivo en el peldaño elegido."""
    n = spec.get("pasos", 4)
    corte = spec.get("corte")  # sin corte se dibuja solo la progresión
    ic = spec.get("iconos", [])
    banda = h * 0.12
    base = h - banda
    x0 = w * 0.08
    pw = (w * 0.84) / n
    ph = (h * 0.62) / n
    s = ""
    for i in range(n):
        alto = ph * (i + 1)
        x, y = x0 + pw * i, base - alto
        s += f'<rect x="{x:.0f}" y="{y:.0f}" width="{pw - 6:.0f}" height="{alto:.0f}" fill="{OLIVA}" opacity="{0.26 + 0.17 * i:.2f}"/>'
        if i < len(ic):
            s += icono(ic[i], x + pw / 2, y + ph * 0.52, min(pw * 0.52, ph * 0.9), OLIVA, ORO)
    if corte is not None:
        xc = x0 + pw * corte
        s += (f'<line x1="{xc:.0f}" y1="{h * 0.10:.0f}" x2="{xc:.0f}" y2="{base + banda * 0.4:.0f}" '
              f'stroke="{ORO}" stroke-width="20" stroke-linecap="round"/>')
    return s

def ruta(spec, w, h):
    """La táctica que choca queda en gris; la alternativa llega al mismo destino en oro."""
    y = h * 0.62
    s = f'<circle cx="{w * 0.09:.0f}" cy="{y:.0f}" r="22" fill="{OLIVA}"/>'
    # la via que no rinde: se detiene contra el muro
    s += f'<line x1="{w * 0.09:.0f}" y1="{y:.0f}" x2="{w * 0.50:.0f}" y2="{y:.0f}" stroke="{GRIS}" stroke-width="18" stroke-linecap="round"/>'
    s += f'<rect x="{w * 0.51:.0f}" y="{h * 0.34:.0f}" width="30" height="{h * 0.44:.0f}" rx="6" fill="{OLIVA}"/>'
    # la alternativa: mismo origen, mismo destino, otro camino
    s += (f'<path d="M {w * 0.09:.0f} {y:.0f} C {w * 0.22:.0f} {h * 0.14:.0f}, {w * 0.72:.0f} {h * 0.10:.0f}, '
          f'{w * 0.86:.0f} {y - h * 0.06:.0f}" fill="none" stroke="{ORO}" stroke-width="17" stroke-linecap="round"/>')
    s += f'<circle cx="{w * 0.88:.0f}" cy="{y:.0f}" r="26" fill="{ORO}"/>'
    if spec.get("icono"):
        s += icono(spec["icono"], w * 0.88, y + h * 0.22, min(w, h) * 0.17, OLIVA, ORO)
    return s

def red(spec, w, h):
    """Nodos periféricos que dependen de un centro: red vecinal, coordinación, enlace."""
    n = spec.get("nodos", 7)
    cx, cy = w / 2, h * 0.52
    r = min(w, h) * 0.34
    s = ""
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang) * 0.86
        s += f'<line x1="{cx:.0f}" y1="{cy:.0f}" x2="{x:.0f}" y2="{y:.0f}" stroke="{ORO}" stroke-width="5" opacity=".75"/>'
        s += icono(spec.get("nodo", "comunidad"), x, y, min(w, h) * 0.13, OLIVA, ORO)
    s += f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{min(w, h) * 0.115:.0f}" fill="{PAPEL}" stroke="{OLIVA}" stroke-width="7"/>'
    s += icono(spec.get("centro", "alerta"), cx, cy, min(w, h) * 0.14, OLIVA, ORO)
    return s


def barras(spec, w, h):
    """Serie sin cifras legibles; el oro marca el tramo que la diapositiva señala."""
    alturas = spec["alturas"]
    acento = set(spec.get("acento", []))
    n = len(alturas)
    banda = h * 0.16
    base = h - banda
    pw = (w * 0.84) / n
    s = f'<line x1="{w * 0.06:.0f}" y1="{base:.0f}" x2="{w * 0.94:.0f}" y2="{base:.0f}" stroke="{OLIVA}" stroke-width="6" stroke-linecap="round"/>'
    for i, v in enumerate(alturas):
        alto = (base - h * 0.12) * max(0.06, min(v, 1.0))
        x = w * 0.08 + pw * i
        s += f'<rect x="{x:.0f}" y="{base - alto:.0f}" width="{pw * 0.66:.0f}" height="{alto:.0f}" rx="5" fill="{ORO if i in acento else OLIVA}" opacity="{1 if i in acento else .55}"/>'
    if spec.get("icono"):
        for i in sorted(acento):
            x = w * 0.08 + pw * i + pw * 0.33
            s += icono(spec["icono"], x, base + banda * 0.48, banda * 0.72, OLIVA, ORO)
    return s


def mapa_puntos(spec, w, h):
    """El mismo plano dos veces: el problema se desplaza en lugar de desaparecer."""
    banda = h * 0.15
    mh = h - banda
    s = ""
    for lado in (0, 1):
        ox = lado * w / 2
        s += f'<rect x="{ox + w * 0.03:.0f}" y="{mh * 0.12:.0f}" width="{w * 0.44:.0f}" height="{mh * 0.74:.0f}" fill="none" stroke="{TENUE}" stroke-width="4"/>'
        for k in range(1, 4):  # trama de manzanas
            s += f'<line x1="{ox + w * 0.03:.0f}" y1="{mh * (0.12 + 0.185 * k):.0f}" x2="{ox + w * 0.47:.0f}" y2="{mh * (0.12 + 0.185 * k):.0f}" stroke="{TENUE}" stroke-width="3"/>'
            s += f'<line x1="{ox + w * (0.03 + 0.11 * k):.0f}" y1="{mh * 0.12:.0f}" x2="{ox + w * (0.03 + 0.11 * k):.0f}" y2="{mh * 0.86:.0f}" stroke="{TENUE}" stroke-width="3"/>'
        fila_y = mh * (0.305 if lado == 0 else 0.49)
        for i in range(9):
            x = ox + w * 0.07 + i * w * 0.045
            s += f'<circle cx="{x:.0f}" cy="{fila_y + (i % 3 - 1) * 9:.0f}" r="11" fill="#9A3B27" opacity=".85"/>'
    s += (f'<path d="M {w * 0.30:.0f} {mh * 0.24:.0f} C {w * 0.46:.0f} {mh * 0.06:.0f}, {w * 0.62:.0f} {mh * 0.10:.0f}, '
          f'{w * 0.74:.0f} {mh * 0.42:.0f}" fill="none" stroke="{ORO}" stroke-width="12" stroke-linecap="round" '
          f'marker-end="url(#pa)"/>')
    s = ('<defs><marker id="pa" viewBox="0 0 12 12" refX="9" refY="6" markerWidth="6" markerHeight="6" '
         f'orient="auto"><path d="M0 0 L12 6 L0 12 z" fill="{ORO}"/></marker></defs>') + s
    return s


def flujo(spec, w, h):
    """Secuencia de pasos: cada uno habilita el siguiente."""
    ic = spec["iconos"]
    n = len(ic)
    acento = set(spec.get("acento", []))
    banda = h * 0.16
    cy = (h - banda) / 2
    paso = w / n
    rad = min(paso * 0.30, (h - banda) * 0.30)
    s = ""
    for i, nombre in enumerate(ic):
        x = paso * (i + 0.5)
        activo = i in acento or not acento
        c, a = _colores(activo)
        s += f'<circle cx="{x:.0f}" cy="{cy:.0f}" r="{rad:.0f}" fill="{PAPEL}" stroke="{OLIVA if activo else GRIS}" stroke-width="6"/>'
        s += icono(nombre, x, cy, rad * 1.2, c, a)
        if i < n - 1:
            s += (f'<line x1="{x + rad * 1.24:.0f}" y1="{cy:.0f}" x2="{paso * (i + 1.5) - rad * 1.32:.0f}" y2="{cy:.0f}" '
                  f'stroke="{ORO}" stroke-width="9" stroke-linecap="round" marker-end="url(#fa)"/>')
    s = ('<defs><marker id="fa" viewBox="0 0 12 12" refX="10" refY="6" markerWidth="5" markerHeight="5" '
         f'orient="auto"><path d="M0 0 L12 6 L0 12 z" fill="{ORO}"/></marker></defs>') + s
    return s


def ciclo(spec, w, h):
    """Proceso que se repite: planificar, ejecutar, evaluar, ajustar."""
    ic = spec["iconos"]
    n = len(ic)
    cx, cy = w / 2, h * 0.52
    r = min(w, h) * 0.32
    s = f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="none" stroke="{ORO}" stroke-width="10" opacity=".55" stroke-dasharray="30 18"/>'
    for i, nombre in enumerate(ic):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
        rad = min(w, h) * 0.115
        s += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rad:.0f}" fill="{PAPEL}" stroke="{OLIVA}" stroke-width="6"/>'
        s += icono(nombre, x, y, rad * 1.2, OLIVA, ORO)
    return s


def jerarquia(spec, w, h):
    """Una instancia superior y las que dependen de ella."""
    ic = spec["iconos"]
    cx = w / 2
    top_y, bot_y = h * 0.24, h * 0.70
    rad = min(w / (len(ic) + 1) * 0.34, h * 0.15)
    s = icono(spec.get("cabeza", "jerarquia"), cx, top_y, rad * 2.2, OLIVA, ORO)
    paso = w / len(ic)
    for i, nombre in enumerate(ic):
        x = paso * (i + 0.5)
        s += (f'<path d="M {cx:.0f} {top_y + rad * 1.25:.0f} C {cx:.0f} {(top_y + bot_y) / 2:.0f}, '
              f'{x:.0f} {(top_y + bot_y) / 2:.0f}, {x:.0f} {bot_y - rad * 1.25:.0f}" fill="none" '
              f'stroke="{ORO}" stroke-width="6" opacity=".7"/>')
        s += f'<circle cx="{x:.0f}" cy="{bot_y:.0f}" r="{rad:.0f}" fill="{PAPEL}" stroke="{OLIVA}" stroke-width="6"/>'
        s += icono(nombre, x, bot_y, rad * 1.2, OLIVA, ORO)
    return s


def balanza(spec, w, h):
    """Dos exigencias que deben sostenerse a la vez."""
    cx, cy = w / 2, h * 0.30
    br = w * 0.30
    s = f'<line x1="{cx:.0f}" y1="{cy:.0f}" x2="{cx:.0f}" y2="{h * 0.84:.0f}" stroke="{OLIVA}" stroke-width="12" stroke-linecap="round"/>'
    s += f'<line x1="{cx - w * 0.10:.0f}" y1="{h * 0.84:.0f}" x2="{cx + w * 0.10:.0f}" y2="{h * 0.84:.0f}" stroke="{OLIVA}" stroke-width="12" stroke-linecap="round"/>'
    s += f'<line x1="{cx - br:.0f}" y1="{cy:.0f}" x2="{cx + br:.0f}" y2="{cy:.0f}" stroke="{OLIVA}" stroke-width="10" stroke-linecap="round"/>'
    for lado, nombre in ((-1, spec["iconos"][0]), (1, spec["iconos"][1])):
        x = cx + br * lado
        s += f'<line x1="{x:.0f}" y1="{cy:.0f}" x2="{x:.0f}" y2="{cy + h * 0.10:.0f}" stroke="{OLIVA}" stroke-width="6"/>'
        s += f'<path d="M {x - w * 0.12:.0f} {cy + h * 0.10:.0f} H {x + w * 0.12:.0f} L {x + w * 0.07:.0f} {cy + h * 0.20:.0f} H {x - w * 0.07:.0f} Z" fill="{ORO}" opacity=".9"/>'
        s += icono(nombre, x, cy + h * 0.32, min(w, h) * 0.17, OLIVA, ORO)
    return s


def linea_tiempo(spec, w, h):
    """Etapas sucesivas con un hito destacado."""
    ic = spec["iconos"]
    n = len(ic)
    acento = set(spec.get("acento", []))
    y = h * 0.50
    x0, x1 = w * 0.12, w * 0.88
    s = f'<line x1="{x0 - w * 0.05:.0f}" y1="{y:.0f}" x2="{x1 + w * 0.05:.0f}" y2="{y:.0f}" stroke="{OLIVA}" stroke-width="8" stroke-linecap="round"/>'
    paso = (x1 - x0) / max(n - 1, 1)
    tam = min(paso * 0.62, h * 0.24)
    for i, nombre in enumerate(ic):
        x = x0 + paso * i
        arriba = i % 2 == 0
        yy = y - h * 0.27 if arriba else y + h * 0.27
        activo = i in acento or not acento
        c, a = _colores(activo)
        s += f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x:.0f}" y2="{yy + (tam / 2 if arriba else -tam / 2):.0f}" stroke="{GRIS}" stroke-width="5"/>'
        s += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="13" fill="{ORO if activo else GRIS}"/>'
        s += icono(nombre, x, yy, tam, c, a)
    return s

ARQUETIPOS = {
    "triangulo": triangulo, "fila": fila, "capas": capas, "embudo": embudo,
    "contraste": contraste, "escalera": escalera, "ruta": ruta, "red": red,
    "barras": barras, "mapa_puntos": mapa_puntos, "flujo": flujo, "ciclo": ciclo,
    "jerarquia": jerarquia, "balanza": balanza, "linea_tiempo": linea_tiempo,
}


def construir(spec: dict, w: int = 1600, h: int = 1200) -> str:
    """Dibuja el diagrama con su título y sus rótulos.

    Ningún arquetipo puede salir sin texto: si el suyo no coloca los rótulos,
    se añade una banda inferior con ellos. Un diagrama mudo no dice nada de la
    diapositiva que acompaña.
    """
    tipo = spec["tipo"]
    if tipo not in ARQUETIPOS:
        raise KeyError(f"arquetipo desconocido: {tipo}. Disponibles: {sorted(ARQUETIPOS)}")

    aplicar_paleta(spec.get("paleta"))
    cuerpo = ARQUETIPOS[tipo](spec, w, h)
    cuerpo += _titulo(spec, w)

    rotulos = _rotulos_de(spec)
    if rotulos and MARCA_ROTULOS not in cuerpo:
        n = len(rotulos)
        cuerpo += _banda_rotulos(spec, w, h,
                                 [w / n * (i + 0.5) for i in range(n)],
                                 h - ROTULO_PX * 1.6)
    svg = _marco(w, h, cuerpo)
    aplicar_paleta(None)      # no dejar la paleta fijada para el siguiente
    return svg


def escribir(spec: dict, destino: Path, w: int = 1600, h: int = 1200) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    svg = destino.with_suffix(".svg")
    svg.write_text(construir(spec, w, h), encoding="utf-8")
    png = destino.with_suffix(".png")
    subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), str(svg), "-o", str(png)], check=True)
    return png
