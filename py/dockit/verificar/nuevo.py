#!/usr/bin/env python3
"""Crea la carpeta de un trabajo nuevo con su BRIEF.md.

    sisifo nuevo <slug> --titulo "..." [--materia "..."]
                                        [--entrega AAAA-MM-DD]
                                        [--entregable salida/X.docx:docx] ...

No pisa nada: si la carpeta ya existe con BRIEF.md, se planta.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

def _buscar_plantilla() -> Path:
    """Sube desde este archivo hasta encontrar plantillas/BRIEF.md.

    Así el script sigue funcionando aunque el paquete se mueva de sitio, que es
    justo lo que pasó al centralizar el código."""
    if v := os.environ.get("TALLER_HOME"):
        c = Path(v) / "plantillas" / "BRIEF.md"
        if c.exists():
            return c
    for padre in Path(__file__).resolve().parents:
        c = padre / "plantillas" / "BRIEF.md"
        if c.exists():
            return c
    return Path(__file__).resolve().parents[3] / "plantillas" / "BRIEF.md"


PLANTILLA = _buscar_plantilla()
SUBDIRS = ("fuentes", "salida", "trabajo")


def slugificar(txt: str) -> str:
    txt = txt.strip().lower()
    txt = re.sub(r"[^a-z0-9]+", "-", txt)
    return txt.strip("-")


def bloque_entregables(specs: list[str]) -> str:
    """'salida/X.docx:docx:8' -> entrada YAML con su mínimo opcional."""
    if not specs:
        specs = ["salida/documento.docx:docx"]
    filas = []
    for spec in specs:
        partes = spec.split(":")
        ruta = partes[0]
        tipo = partes[1] if len(partes) > 1 else Path(ruta).suffix.lstrip(".")
        minimo = partes[2] if len(partes) > 2 else None
        clave = "minimo_diapositivas" if tipo == "pptx" else "minimo_paginas"
        filas.append(
            f"  - archivo: {ruta}\n"
            f"    tipo: {tipo}\n"
            f"    {clave}: {minimo or 'null'}"
        )
    return "\n".join(filas)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("slug")
    p.add_argument("--titulo", required=True)
    p.add_argument("--materia")
    p.add_argument("--docente")
    p.add_argument("--entrega", help="AAAA-MM-DD")
    p.add_argument("--entregable", action="append", default=[],
                   help="ruta[:tipo[:minimo]], repetible")
    p.add_argument("--raiz", type=Path, default=None,
                   help="dónde crear la carpeta (por defecto, donde estés)")
    args = p.parse_args()

    raiz = (args.raiz or Path.cwd()).resolve()
    slug = slugificar(args.slug)
    destino = raiz / slug
    brief = destino / "BRIEF.md"

    if brief.exists():
        print(f"ya existe {brief} — no se toca", file=sys.stderr)
        return 1

    if not PLANTILLA.exists():
        print(f"falta la plantilla {PLANTILLA}", file=sys.stderr)
        return 1

    for sub in SUBDIRS:
        (destino / sub).mkdir(parents=True, exist_ok=True)

    texto = PLANTILLA.read_text(encoding="utf-8")
    texto = texto.replace("SLUG", slug).replace("TITULO", args.titulo)
    for clave, valor in (("materia", args.materia),
                         ("docente", args.docente),
                         ("entrega", args.entrega)):
        if valor:
            texto = re.sub(rf"^{clave}: null.*$", f"{clave}: {valor}",
                           texto, count=1, flags=re.M)

    # sustituye el bloque de entregables de ejemplo
    texto = re.sub(
        r"entregables:\n(?:  [-#].*\n|    .*\n)+",
        "entregables:\n" + bloque_entregables(args.entregable) + "\n",
        texto, count=1,
    )

    brief.write_text(texto, encoding="utf-8")
    (destino / "fuentes" / ".gitkeep").touch()

    print(f"creado {destino.relative_to(raiz)}/")
    for sub in SUBDIRS:
        print(f"  {sub}/")
    print(f"  BRIEF.md   <- llénalo antes de pedir nada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
