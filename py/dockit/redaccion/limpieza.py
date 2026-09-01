"""Descarta el texto de servicio de los PDF académicos.

Cabeceras de revista, licencias, DOI sueltos, marcas de descarga y datos de
contacto no son contenido: si entran en el índice, el modelo los recupera como
si lo fueran. Un caso real acabó atribuyendo una afirmación técnica al editor
de la revista, cuyo nombre venía en el machote de la primera página.
"""
from __future__ import annotations

import re

PATRONES = [
    r"\bassociate editor\b",
    r"\bcoordinating the review of this manuscript\b",
    # El maquetado a dos columnas parte el pie de página y mete el trozo en
    # mitad de una frase del cuerpo; hay que reconocer también los fragmentos.
    r"\bapproving it for publication was\b",
    r"\bwas coordinated by\b.*\beditor\b",
    r"\bcreative commons\b",
    r"\bthis work is licensed under\b",
    r"\bdownloaded on\b.*\bfrom\b.*\b(xplore|ieee|jstor)\b",
    r"\brestrictions apply\b",
    r"^\s*volume\s+\d+,?\s*\d{4}\s*$",
    r"\bdigital object identifier\b",
    r"\bcorresponding author\b",
    r"\btranslations and content mining are permitted\b",
    r"^\s*\d{4}-\d{3,4}\s*(©|\(c\))",
    r"\ball rights reserved\b",
    r"^\s*(page|página)\s+\d+\s*$",
    r"^\s*doi:?\s*10\.\d{4,}",
    r"\bsee discussions, stats, and author profiles\b",   # ResearchGate
    r"\bresearchgate\b",
]
RE_RUIDO = re.compile("|".join(PATRONES), re.IGNORECASE)

# Un «(2020)» suelto que quedó al retirar la clave de la cita. Se lleva por
# delante la coma que lo seguía: «Según (2020), los oráculos» dejaba un
# «Según, los oráculos» que no es español.
RE_ANIO_SUELTO = re.compile(r"\s*\(\s*\d{4}[a-z]?\s*\)\s*,?")


def es_ruido(linea: str) -> bool:
    l = linea.strip()
    if not l:
        return False
    if RE_RUIDO.search(l):
        return True
    # una línea corta que es casi toda dígitos y símbolos no dice nada
    if len(l) < 40:
        letras = sum(c.isalpha() for c in l)
        if letras and letras / len(l) < 0.45:
            return True
    return False


def limpiar(texto: str) -> str:
    """Quita las líneas de servicio, conservando todo lo demás."""
    utiles = [l for l in texto.splitlines() if not es_ruido(l)]
    if not utiles:
        return texto        # ante la duda, conservar: perder contenido es peor
    return "\n".join(utiles)


def sin_restos_de_cita(texto: str) -> str:
    """Limpia los «(2020)» que quedan al retirar la clave de una cita."""
    t = RE_ANIO_SUELTO.sub("", texto)
    t = re.sub(r"\s+([.,;:])", r"\1", t)
    t = re.sub(r"([.,;:])\s*\1+", r"\1", t)
    return re.sub(r" {2,}", " ", t).strip()
