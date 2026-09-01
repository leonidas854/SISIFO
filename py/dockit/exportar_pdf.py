#!/usr/bin/env python3
"""Exporta los entregables a PDF con los índices ya calculados.

    exportar_pdf.py --carpeta <t> [--archivo salida/informe.docx]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dockit.generadores import a_pdf  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--carpeta", type=Path, required=True)
    p.add_argument("--archivo", help="por defecto, todos los .docx de salida/")
    args = p.parse_args()

    carpeta = args.carpeta.resolve()
    if args.archivo:
        docs = [carpeta / args.archivo]
    else:
        docs = sorted((carpeta / "salida").glob("*.docx"))
    if not docs:
        print("no hay .docx en salida/ — usa 'sisifo producir' antes",
              file=sys.stderr)
        return 1

    for doc in docs:
        if not doc.exists():
            print(f"[falla] {doc.name}: no existe", file=sys.stderr)
            return 1
        try:
            destino = a_pdf.exportar(str(doc))
        except Exception as e:
            print(f"[falla] {doc.name}: {e}", file=sys.stderr)
            return 1
        print(f"[ ok ] {Path(destino).relative_to(carpeta)} — índices calculados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
