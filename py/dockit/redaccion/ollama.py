"""Cliente mínimo de ollama para generación local.

Solo lo que hace falta: mandar un prompt y recibir texto. Sin dependencias
externas —urllib de la biblioteca estándar— porque este puente tiene que
seguir funcionando aunque cambie el resto del entorno.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODELO = os.environ.get("SISIFO_MODELO", "llama3.2")
TIEMPO_MAX = 600


class ErrorOllama(RuntimeError):
    pass


def disponible(modelo: str | None = None) -> bool:
    try:
        with urllib.request.urlopen(f"{URL}/api/tags", timeout=10) as r:
            etiquetas = json.load(r)
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return False
    if modelo is None:
        return True
    nombres = {m.get("name", "").split(":")[0] for m in etiquetas.get("models", [])}
    return modelo.split(":")[0] in nombres


def generar(prompt: str, modelo: str | None = None, temperatura: float = 0.2,
            maximo: int = 900) -> str:
    """Genera texto. Temperatura baja: se busca fidelidad, no creatividad."""
    cuerpo = json.dumps({
        "model": modelo or MODELO,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperatura, "num_predict": maximo},
    }).encode("utf-8")
    pet = urllib.request.Request(
        f"{URL}/api/generate", data=cuerpo,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(pet, timeout=TIEMPO_MAX) as r:
            datos = json.load(r)
    except urllib.error.URLError as e:
        raise ErrorOllama(f"¿está ollama corriendo? {e}") from e
    if "error" in datos:
        raise ErrorOllama(datos["error"])
    return (datos.get("response") or "").strip()
