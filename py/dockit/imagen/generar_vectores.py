#!/usr/bin/env python3
"""Dibuja localmente todas las opciones conceptuales de un plan (motor "vector").

No usa GPU ni modelo generativo: cada diapositiva declara su diagrama en una línea de
JSON y `diagramas.py` lo resuelve como SVG determinista en la paleta de la plantilla.

    python3 herramientas/generar_vectores.py prompts/tema03_plan.json imagenes/
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import diagramas  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("plan", type=Path)
    p.add_argument("salida", type=Path)
    p.add_argument("--tema", type=int, action="append", dest="temas")
    p.add_argument("--force", action="store_true")
    p.add_argument("--ancho", type=int, default=1600)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    trabajos = plan["trabajos"] if isinstance(plan, dict) else plan

    hechos = saltados = fallos = 0
    for t in trabajos:
        if t.get("motor") != "vector":
            continue
        if args.temas and int(t["tema"]) not in args.temas:
            continue
        destino = args.salida / f"tema{int(t['tema']):02d}" / (
            f"diapo{int(t['diapositiva']):02d}_op{int(t['opcion'])}"
        )
        if destino.with_suffix(".png").exists() and not args.force:
            saltados += 1
            continue
        rel = t.get("relacion", "4:3")
        ancho = args.ancho
        alto = int(ancho * 3 / 4) if rel == "4:3" else int(ancho * 9 / 16)
        try:
            if t.get("archivo_svg"):
                # diagrama dibujado a mano para esta diapositiva concreta
                origen = (args.plan.parent.parent / t["archivo_svg"]).resolve()
                destino.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    ["rsvg-convert", "-w", str(ancho), "-h", str(alto),
                     str(origen), "-o", str(destino.with_suffix(".png"))], check=True)
            else:
                diagramas.escribir(t["spec"], destino, ancho, alto)
            hechos += 1
        except Exception as exc:  # el plan es editable a mano: informar sin abortar el lote
            fallos += 1
            print(
                f"error tema {t['tema']} diapo {t['diapositiva']:02d} op{t['opcion']}: {exc}",
                file=sys.stderr,
            )

    print(f"vectores: {hechos} dibujados, {saltados} ya existían, {fallos} con error")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
