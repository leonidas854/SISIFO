#!/usr/bin/env python3
"""Produce los entregables de un trabajo a partir de su guion.

    producir.py --carpeta <t> [--guion guion.json] [--tipo docx,pptx,xlsx]

Lee el guion, la bibliografía y las citas en texto de la carpeta, y escribe
cada entregable en salida/. Si el guion cita una clave que no está en la
bibliografía, se planta: es la misma barrera que en la verificación.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dockit.generadores import GuionInvalido, generar_desde_guion  # noqa: E402


def cargar_json(p: Path, defecto):
    if not p.exists():
        return defecto
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"{p} no es JSON válido: {e}")


def formato_del_brief(carpeta: Path) -> dict:
    brief = carpeta / "BRIEF.md"
    if not brief.exists():
        return {}
    try:
        import re

        import yaml
        m = re.match(r"^---\n(.*?)\n---\n", brief.read_text(encoding="utf-8"), re.S)
        return (yaml.safe_load(m.group(1)) or {}).get("formato") or {} if m else {}
    except Exception:
        return {}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--carpeta", type=Path, required=True)
    p.add_argument("--guion", default="guion.json")
    p.add_argument("--tipo", help="coma-separado; por defecto, el del guion")
    args = p.parse_args()

    carpeta = args.carpeta.resolve()
    ruta_guion = carpeta / args.guion
    if not ruta_guion.exists():
        print(f"no hay {ruta_guion}.\n"
              f"El guion describe el documento: títulos, párrafos, tablas,\n"
              f"figuras y dónde va cada cita. Ejemplo mínimo:\n"
              f'  {{"tipo":"docx","titulo":"...","bloques":['
              f'{{"clase":"titulo","nivel":1,"texto":"Introducción"}}]}}',
              file=sys.stderr)
        return 1

    guion = cargar_json(ruta_guion, None)
    refs = cargar_json(carpeta / "fuentes" / "biblioteca.json", [])
    en_texto = cargar_json(carpeta / "fuentes" / "citas_en_texto.json", {})

    # bibliografia.py deja los dos mapas ya emparejados por citeproc: no hay
    # que adivinar qué entrada corresponde a qué clave
    bibliografia = cargar_json(carpeta / "fuentes" / "referencias_apa.json", {})
    if not bibliografia:
        if en_texto:
            print("aviso: falta fuentes/referencias_apa.json — ejecuta 'taller bib'",
                  file=sys.stderr)
        bibliografia = {r["id"]: r.get("title", r["id"]) for r in refs if r.get("id")}

    tipos = ([t.strip() for t in args.tipo.split(",")] if args.tipo
             else [guion.get("tipo", "docx")])
    formato = formato_del_brief(carpeta)

    salida = carpeta / "salida"
    salida.mkdir(parents=True, exist_ok=True)
    base = ruta_guion.stem if ruta_guion.stem != "guion" else carpeta.name

    for tipo in tipos:
        g = dict(guion, tipo=tipo)
        destino = salida / f"{base}.{tipo}"
        try:
            r = generar_desde_guion(g, str(destino), bibliografia, en_texto, formato)
        except GuionInvalido as e:
            print(f"[falla] {tipo}: {e}", file=sys.stderr)
            return 1
        unidad = {"docx": "páginas", "pptx": "diapositivas",
                  "xlsx": "hojas"}.get(tipo, "unidades")
        aprox = "~" if r.get("unidades_estimadas") else ""
        print(f"[ ok ] {destino.relative_to(carpeta)} — {aprox}{r['unidades']} {unidad}")

    print("\nrevisa el resultado en OnlyOffice y luego: taller verificar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
