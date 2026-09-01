"""Anclaje: que lo que escriba el modelo local no pueda inventarse.

Dos reglas, aplicadas después de generar y antes de aceptar nada:

1. Solo se citan claves ya verificadas contra Crossref o DataCite. Cualquier
   otra se descarta del texto: el modelo no puede introducir bibliografía.
2. Toda frase con un dato duro se convierte en una afirmación que hay que
   respaldar con una cita literal de los pasajes recuperados. Si ningún pasaje
   la respalda, se deja sin fuente y el verificador la bloqueará — nunca se le
   asigna una fuente por parecido vago.
"""
from __future__ import annotations

import re
import unicodedata

# Cada modelo cita a su manera: llama3.2 usa paréntesis, qwen2.5 corchetes, y
# a veces ponen la clave en mayúscula. Todas cuentan como cita.
RE_CLAVE = re.compile(r"[\(\[]?\b([A-Za-z][A-Za-z0-9]*\d{4}[A-Za-z0-9]*)\b[\)\]]?")
RE_FRASE = re.compile(r"[^.!?]+[.!?]")
RE_DATO = re.compile(r"\d")
MIN_SOLAPE = 0.18          # por debajo, el pasaje no respalda la frase


def normalizar(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = s.encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", s)).strip()


def filtrar_citas(texto: str, verificadas: set[str]) -> tuple[str, list[str]]:
    """Quita del texto toda clave que no esté verificada."""
    descartadas: list[str] = []

    indice = {c.lower(): c for c in verificadas}

    def sustituir(m: re.Match) -> str:
        clave = indice.get(m.group(1).lower())
        if clave:
            return m.group(0)
        descartadas.append(m.group(1))
        return ""

    limpio = RE_CLAVE.sub(sustituir, texto)
    limpio = re.sub(r"\(\s*\)", "", limpio)
    limpio = re.sub(r" {2,}", " ", limpio)
    return re.sub(r"\s+([.,;:])", r"\1", limpio).strip(), descartadas


def normalizar_citas(texto: str, verificadas: set[str]) -> tuple[str, list[str]]:
    """Saca las claves del texto y devuelve (texto limpio, claves citadas).

    El modelo local escribe indistintamente «(clave2020)» y «según clave2020»;
    las dos formas cuentan. Sacarlas del cuerpo importa por dos razones: la
    cita definitiva la pone citeproc con el formato APA, y una clave como
    `breiki2020trustworthy` lleva un año dentro que la detección de cifras
    confundiría con un dato que necesita respaldo.
    """
    citadas: list[str] = []
    indice = {c.lower(): c for c in verificadas}

    def sustituir(m: re.Match) -> str:
        clave = indice.get(m.group(1).lower())
        if clave is None:
            return m.group(0)
        if clave not in citadas:
            citadas.append(clave)
        return ""

    limpio = RE_CLAVE.sub(sustituir, texto)
    limpio = re.sub(r"\(\s*\)", "", limpio)
    limpio = re.sub(r"\s+([.,;:])", r"\1", limpio)
    limpio = re.sub(r"([.,;:])\1+", r"\1", limpio)
    return re.sub(r" {2,}", " ", limpio).strip(), citadas


def _solape(frase: str, pasaje: str) -> float:
    """Cuántas palabras de la frase aparecen en el pasaje."""
    a = set(normalizar(frase).split())
    b = set(normalizar(pasaje).split())
    if not a:
        return 0.0
    return len(a & b) / len(a)


def _mejor_pasaje(frase: str, pasajes: list[dict], verificadas: set[str]):
    mejor, punt = None, 0.0
    for p in pasajes:
        if p.get("fuente") not in verificadas:
            continue
        s = _solape(frase, p.get("texto", ""))
        if s > punt:
            mejor, punt = p, s
    return (mejor, punt) if punt >= MIN_SOLAPE else (None, punt)


def _cita_literal(frase: str, pasaje: str, palabras: int = 18) -> str:
    """Toma del pasaje la ventana más parecida a la frase, copiada tal cual."""
    tokens = pasaje.split()
    if len(tokens) <= palabras:
        return pasaje.strip()
    mejor, punt = tokens[:palabras], 0.0
    for i in range(0, len(tokens) - palabras + 1, 3):
        ventana = tokens[i:i + palabras]
        s = _solape(frase, " ".join(ventana))
        if s > punt:
            mejor, punt = ventana, s
    return " ".join(mejor).strip()


def extraer_afirmaciones(texto: str, pasajes: list[dict],
                         verificadas: set[str], prefijo: str = "a") -> list[dict]:
    """Convierte en afirmaciones verificables las frases con datos duros."""
    salida: list[dict] = []
    for frase in RE_FRASE.findall(texto) or ([texto] if texto.strip() else []):
        frase = frase.strip()
        if not frase:
            continue
        # el año dentro de una clave de cita no es un dato del texto
        sin_claves = RE_CLAVE.sub("", frase)
        if not RE_DATO.search(sin_claves):
            continue
        pasaje, _ = _mejor_pasaje(frase, pasajes, verificadas)
        salida.append({
            "id": f"{prefijo}{len(salida) + 1}",
            "texto": frase,
            "fuente": pasaje["fuente"] if pasaje else "",
            "cita": _cita_literal(frase, pasaje["texto"]) if pasaje else "",
        })
    return salida
