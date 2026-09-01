"""Puente hacia el generador PPTX de Node (pptxgenjs).

Por qué existe: python-pptx no sabe crear gráficos nativos ni notas del orador
con soltura, y el requisito es que la diapositiva quede **editable** —títulos,
cifras, tablas y citas como objetos de PowerPoint, no incrustados en una
imagen—. pptxgenjs sí lo hace, así que se delega en él cuando está instalado.

Es un adaptador: cumple el mismo contrato que `pptx.py` y se puede sustituir
sin tocar nada más.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import guion as G

RAIZ = Path(__file__).resolve().parents[3]      # raíz del repo
GUION_JS = Path(__file__).with_name("pptx.js")
TIEMPO_MAX = 180


class ErrorGeneradorNode(RuntimeError):
    """Node existe pero la generación falló; el mensaje dice por qué."""


def _node() -> str | None:
    return shutil.which("node")


def disponible() -> bool:
    """¿Se puede generar con Node aquí y ahora?

    Comprueba las tres cosas que hacen falta, sin lanzar: el intérprete, el
    script y la dependencia instalada. Si falta cualquiera, se usa python-pptx.
    """
    if not _node() or not GUION_JS.exists():
        return False
    return (RAIZ / "node_modules" / "pptxgenjs").is_dir()


def generar(guion: dict, destino: str, bibliografia: dict[str, str],
            en_texto: dict[str, str], formato: dict | None = None) -> dict:
    G.validar(guion, set(bibliografia) if bibliografia else None)

    node = _node()
    if not node:
        raise ErrorGeneradorNode("no encuentro Node en el PATH")
    if not GUION_JS.exists():
        raise ErrorGeneradorNode(f"falta {GUION_JS}")

    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    peticion = {
        "guion": guion,
        "destino": str(Path(destino).resolve()),
        "bibliografia": bibliografia or {},
        "en_texto": en_texto or {},
        "formato": formato or {},
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8",
                                     delete=False) as f:
        json.dump(peticion, f, ensure_ascii=False)
        entrada = f.name
    try:
        r = subprocess.run([node, str(GUION_JS), entrada],
                           capture_output=True, text=True, timeout=TIEMPO_MAX,
                           cwd=str(RAIZ))
    except subprocess.TimeoutExpired:
        raise ErrorGeneradorNode(
            f"la generación tardó más de {TIEMPO_MAX}s") from None
    finally:
        os.unlink(entrada)

    if r.returncode != 0:
        detalle = (r.stderr or r.stdout or "sin detalle").strip().splitlines()
        raise ErrorGeneradorNode(
            f"pptxgenjs falló: {detalle[-1] if detalle else 'sin detalle'}")

    # el script imprime el resultado en JSON; si no, se mide el archivo
    try:
        salida = json.loads(r.stdout.strip().splitlines()[-1])
        if isinstance(salida, dict) and "unidades" in salida:
            return {"ruta": destino, "unidades": int(salida["unidades"])}
    except (json.JSONDecodeError, IndexError, ValueError, KeyError):
        pass

    if not Path(destino).exists():
        raise ErrorGeneradorNode("Node terminó bien pero no escribió el archivo")
    from pptx import Presentation
    return {"ruta": destino, "unidades": len(Presentation(destino).slides._sldIdLst)}
