"""Generadores de entregables a partir de un guion común."""
from __future__ import annotations

import os
import re
from pathlib import Path

from . import guion as _guion
from .guion import GuionInvalido, validar

_POR_TIPO = {}


def destino_libre(destino: str, *, variante: str | None = None,
                  sobrescribir: bool = False) -> str:
    """Devuelve una ruta que no destruya trabajo previo.

    El usuario abre el entregable en OnlyOffice, lo retoca y lo usa. Si la
    siguiente pasada lo pisara en silencio, perdería esa revisión. Por eso:

    - `variante`: un nombre propio para esta salida (p. ej. el tema que se
      está desarrollando) -> `diapos-tema3.pptx`
    - si el archivo ya existe, se numera la pasada -> `diapos-v2.pptx`
    - `sobrescribir=True` solo cuando se pide explícitamente
    """
    p = Path(destino)
    if variante:
        limpio = re.sub(r"[^\w.-]+", "-", variante.strip()).strip("-")
        if limpio:
            p = p.with_name(f"{p.stem}-{limpio}{p.suffix}")
    if sobrescribir or not p.exists():
        return str(p)
    for n in range(2, 1000):
        cand = p.with_name(f"{p.stem}-v{n}{p.suffix}")
        if not cand.exists():
            return str(cand)
    raise GuionInvalido(f"demasiadas versiones de {p.name}; limpia la carpeta")



def _cargar(tipo: str):
    if tipo not in _POR_TIPO:
        if tipo == "docx":
            from . import docx as m
        elif tipo == "pptx":
            # pptxgenjs hace gráficos nativos y notas del orador; python-pptx
            # es el respaldo cuando no hay Node. Ambos dejan el texto editable.
            from . import pptx_node
            if pptx_node.disponible() and os.environ.get("SISIFO_PPTX") != "python":
                m = pptx_node
            else:
                from . import pptx as m
        elif tipo == "xlsx":
            from . import xlsx as m
        else:
            raise GuionInvalido(f"no sé generar «{tipo}»")
        _POR_TIPO[tipo] = m
    return _POR_TIPO[tipo]


def generar_desde_guion(guion: dict, destino: str,
                        bibliografia: dict[str, str] | None = None,
                        en_texto: dict[str, str] | None = None,
                        formato: dict | None = None,
                        variante: str | None = None,
                        sobrescribir: bool = False) -> dict:
    """Punto único de entrada: elige el generador según el tipo del guion.

    Nunca pisa un entregable anterior salvo que se pida (ver `destino_libre`).
    """
    tipo = guion.get("tipo")
    if tipo not in ("docx", "pptx", "xlsx"):
        raise GuionInvalido(f"tipo de salida no soportado todavía: {tipo!r}")

    # Citable = tiene entrada en la bibliografía Y forma de cita en el texto.
    # Las dos las produce citeproc solo con las referencias verificadas, así que
    # una referencia sin comprobar no puede colarse en el documento.
    #
    # Ojo con la diferencia: en_texto=None es "no me pasaron el mapa, no puedo
    # comprobar"; en_texto={} es "no hay ninguna referencia verificada", y
    # entonces cualquier cita tiene que fallar.
    if en_texto is not None:
        for i, b in enumerate(guion.get("bloques") or [], 1):
            for c in b.get("citas") or []:
                if c not in en_texto:
                    raise GuionInvalido(
                        f"bloque {i} cita «{c}», que no tiene forma de cita en el "
                        f"texto: no está entre las referencias verificadas")
    destino = destino_libre(destino, variante=variante, sobrescribir=sobrescribir)
    return _cargar(tipo).generar(guion, destino, bibliografia or {},
                                 en_texto or {}, formato)


__all__ = ["generar_desde_guion", "destino_libre", "validar",
           "GuionInvalido"]
