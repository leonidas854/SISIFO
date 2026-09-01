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


def destino_declarado(brief: dict, tipo: str, nombre_carpeta: str) -> str:
    """Ruta del entregable de ese tipo, según el BRIEF.

    El BRIEF es el contrato: si declara `salida/informe.docx`, ese es el
    archivo que el verificador buscará después. Escribir otro nombre deja el
    trabajo hecho pero marcado como incompleto.
    """
    for ent in (brief or {}).get("entregables") or []:
        archivo = (ent or {}).get("archivo")
        if not archivo:
            continue
        declarado = (ent.get("tipo") or Path(archivo).suffix.lstrip(".")).lower()
        if declarado == tipo:
            return archivo
    return f"salida/{nombre_carpeta}.{tipo}"


def cabecera_del_brief(carpeta: Path) -> dict:
    """Cabecera YAML completa del BRIEF, o vacío si no se puede leer."""
    brief = carpeta / "BRIEF.md"
    if not brief.exists():
        return {}
    try:
        import re

        import yaml
        m = re.match(r"^---\n(.*?)\n---\n", brief.read_text(encoding="utf-8"), re.S)
        return (yaml.safe_load(m.group(1)) or {}) if m else {}
    except Exception:
        return {}


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
    p.add_argument("--variante",
                   help="nombre de esta salida, p. ej. el tema que desarrollas: "
                        "diapos-tema3.pptx")
    p.add_argument("--sobrescribir", action="store_true",
                   help="pisa el archivo anterior (por defecto se numera)")
    p.add_argument("--estilo",
                   help="tema visual de las hojas de cálculo; "
                        "'--estilo ?' los lista")
    args = p.parse_args()

    if args.estilo == "?":
        from dockit.generadores import estilos
        print("temas disponibles:")
        for nombre, desc in estilos.listar():
            print(f"  {nombre:<12} {desc}")
        return 0

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
            print("aviso: falta fuentes/referencias_apa.json — ejecuta 'sisifo bib'",
                  file=sys.stderr)
        bibliografia = {r["id"]: r.get("title", r["id"]) for r in refs if r.get("id")}

    tipos = ([t.strip() for t in args.tipo.split(",")] if args.tipo
             else [guion.get("tipo", "docx")])
    formato = formato_del_brief(carpeta)
    formato["_trabajo"] = carpeta.name          # semilla estable del tema visual
    if args.estilo:
        formato["estilo"] = args.estilo

    (carpeta / "salida").mkdir(parents=True, exist_ok=True)
    brief = cabecera_del_brief(carpeta)
    base = ruta_guion.stem if ruta_guion.stem != "guion" else carpeta.name

    # el .pptx tiene su propio guion condensado, si el redactor lo dejó
    diapos = cargar_json(carpeta / "guion_diapos.json", None)

    for tipo in tipos:
        base_guion = diapos if (tipo == "pptx" and diapos) else guion
        g = dict(base_guion, tipo=tipo)
        destino = carpeta / destino_declarado(brief, tipo, base)
        try:
            r = generar_desde_guion(g, str(destino), bibliografia, en_texto,
                                    formato, variante=args.variante,
                                    sobrescribir=args.sobrescribir)
        except GuionInvalido as e:
            print(f"[falla] {tipo}: {e}", file=sys.stderr)
            return 1
        unidad = {"docx": "páginas", "pptx": "diapositivas",
                  "xlsx": "hojas"}.get(tipo, "unidades")
        aprox = "~" if r.get("unidades_estimadas") else ""
        escrito = Path(r["ruta"])
        extra = f" · estilo {r['estilo']}" if r.get("estilo") else ""
        aviso = ""
        if escrito.name != destino.name:
            aviso = "   (no pisé el anterior)"
        print(f"[ ok ] {escrito.relative_to(carpeta)} — "
              f"{aprox}{r['unidades']} {unidad}{extra}{aviso}")

    print("\nrevisa el resultado en OnlyOffice y luego: sisifo verificar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
