"""Puerto y adaptadores para medir la relación entre una idea y una visual."""

from __future__ import annotations

import json
import difflib
import math
import os
import re
import urllib.error
import urllib.request
from collections import Counter
from typing import Protocol, Sequence

from .dominio import PlanVisual, Visual, normalizar


STOPWORDS = {
    "a", "al", "ante", "bajo", "cada", "como", "con", "contra", "de",
    "del", "desde", "donde", "dos", "e", "el", "ella", "en", "entre",
    "es", "esta", "este", "estos", "ha", "hacia", "la", "las", "lo",
    "los", "mas", "no", "o", "para", "pero", "por", "que", "se", "sin",
    "sobre", "son", "su", "sus", "todo", "tres", "un", "una", "y",
}


class PuertoSemantico(Protocol):
    nombre: str

    def comparar(self, pares: Sequence[tuple[str, str]]) -> list[float]: ...


def _tokens(texto: str) -> Counter[str]:
    return Counter(
        p for p in normalizar(texto).split()
        if len(p) >= 3 and p not in STOPWORDS
    )


def _coseno_contadores(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    producto = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return producto / (na * nb) if na and nb else 0.0


def _coseno_difuso(a: Counter[str], b: Counter[str]) -> float:
    """Aproxima flexiones cercanas (integridad/íntegra, traza/trazable).

    Solo se usa en el fallback sin embeddings. El emparejamiento es voraz y
    conservador para no convertir dos palabras cortas parecidas en evidencia
    semántica.
    """
    if not a or not b:
        return 0.0
    disponibles = set(b)
    producto = 0.0
    for izquierda, veces in a.items():
        mejor, palabra = 0.0, None
        for derecha in disponibles:
            proporcion = difflib.SequenceMatcher(None, izquierda, derecha).ratio()
            prefijo = min(len(izquierda), len(derecha), 5)
            if prefijo >= 4 and izquierda[:prefijo] == derecha[:prefijo]:
                proporcion = max(proporcion, 0.78)
            if proporcion > mejor:
                mejor, palabra = proporcion, derecha
        if mejor >= 0.68 and palabra is not None:
            producto += veces * b[palabra] * mejor
            disponibles.remove(palabra)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return producto / (na * nb) if na and nb else 0.0


def _bigramas(texto: str) -> set[str]:
    palabras = normalizar(texto).split()
    return {f"{a} {b}" for a, b in zip(palabras, palabras[1:])}


class SemanticaLexica:
    """Alternativa local determinista para pruebas y equipos sin Ollama.

    No pretende comprender sinónimos. Por eso el resultado del fallback se
    presenta como aproximado y los planes deben declarar conceptos explícitos.
    """

    nombre = "léxica local"

    def comparar(self, pares: Sequence[tuple[str, str]]) -> list[float]:
        salida: list[float] = []
        for esperado, visual in pares:
            ta, tb = _tokens(esperado), _tokens(visual)
            coseno = max(_coseno_contadores(ta, tb), _coseno_difuso(ta, tb))
            ba, bb = _bigramas(esperado), _bigramas(visual)
            bigramas = len(ba & bb) / len(ba | bb) if ba and bb else 0.0
            # El coseno captura conceptos compartidos; los bigramas premian una
            # relación explícita y evitan aprobar por una sola palabra genérica.
            salida.append(min(1.0, 0.85 * coseno + 0.15 * bigramas))
        return salida


def _coseno_vectores(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or len(a) != len(b):
        return 0.0
    producto = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return producto / (na * nb) if na and nb else 0.0


class SemanticaOllama:
    nombre = "bge-m3 (Ollama)"

    def __init__(
        self,
        url: str | None = None,
        modelo: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.url = url or os.environ.get(
            "SISIFO_OLLAMA_URL", "http://localhost:11434/api/embed"
        )
        self.modelo = modelo or os.environ.get("SISIFO_EMBED_MODEL", "bge-m3")
        self.timeout = timeout

    def _embeder(self, textos: list[str]) -> list[list[float]]:
        cuerpo = json.dumps(
            {"model": self.modelo, "input": textos}, ensure_ascii=False
        ).encode("utf-8")
        peticion = urllib.request.Request(
            self.url, data=cuerpo,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(peticion, timeout=self.timeout) as respuesta:
                datos = json.loads(respuesta.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama no respondió en {self.url}: {exc}") from exc
        if datos.get("error"):
            raise RuntimeError(f"Ollama: {datos['error']}")
        vectores = datos.get("embeddings") or []
        if len(vectores) != len(textos):
            raise RuntimeError(
                f"Ollama devolvió {len(vectores)} vectores para {len(textos)} textos"
            )
        return vectores

    def comparar(self, pares: Sequence[tuple[str, str]]) -> list[float]:
        if not pares:
            return []
        textos: list[str] = []
        for esperado, visual in pares:
            textos.extend((esperado, visual))
        vectores = self._embeder(textos)
        return [
            max(0.0, min(1.0, _coseno_vectores(vectores[i], vectores[i + 1])))
            for i in range(0, len(vectores), 2)
        ]


def pares_del_plan(plan: PlanVisual) -> tuple[list[Visual], list[tuple[str, str]]]:
    visuales: list[Visual] = []
    pares: list[tuple[str, str]] = []
    for visual in plan.visuales:
        if visual.tipo in {"portada", "ninguno"}:
            continue
        esperado = visual.proposito
        representado = " ".join(
            (
                visual.concepto_visual,
                " ".join(visual.conceptos),
                visual.texto_alternativo,
                visual.prompt,
            )
        ).strip()
        if esperado and representado:
            visuales.append(visual)
            pares.append((esperado, representado))
    return visuales, pares


def puntuar_plan(
    plan: PlanVisual,
    modo: str = "auto",
) -> tuple[dict[tuple[int, int], float], str, str | None]:
    """Puntúa el plan y devuelve (mapa, proveedor, aviso_de_fallback)."""
    visuales, pares = pares_del_plan(plan)
    if not pares or modo == "ninguno":
        return {}, "desactivada", None

    aviso = None
    if modo in {"auto", "ollama"}:
        proveedor: PuertoSemantico = SemanticaOllama()
        try:
            valores = proveedor.comparar(pares)
            return {v.clave: p for v, p in zip(visuales, valores)}, proveedor.nombre, None
        except RuntimeError as exc:
            if modo == "ollama":
                raise
            aviso = f"no se pudo usar bge-m3 ({exc}); se usó comparación léxica"

    proveedor = SemanticaLexica()
    valores = proveedor.comparar(pares)
    return {v.clave: p for v, p in zip(visuales, valores)}, proveedor.nombre, aviso
