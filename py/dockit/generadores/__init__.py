"""Generadores de entregables a partir de un guion común."""
from __future__ import annotations

from . import guion as _guion
from .guion import GuionInvalido, validar

_POR_TIPO = {}


def _cargar(tipo: str):
    if tipo not in _POR_TIPO:
        if tipo == "docx":
            from . import docx as m
        elif tipo == "pptx":
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
                        formato: dict | None = None) -> dict:
    """Punto único de entrada: elige el generador según el tipo del guion."""
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
    return _cargar(tipo).generar(guion, destino, bibliografia or {},
                                 en_texto or {}, formato)


__all__ = ["generar_desde_guion", "validar", "GuionInvalido"]
