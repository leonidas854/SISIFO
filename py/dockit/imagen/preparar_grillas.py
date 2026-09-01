#!/usr/bin/env python3
"""Agrupa los planes en solicitudes de grillas fotográficas para imagegen."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from componer_laminas import partir_por_diapositiva


ROOT = Path(__file__).resolve().parents[1]


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("planes", type=Path, nargs="+")
    parser.add_argument("--salida", type=Path, default=ROOT / "paneles" / "trabajos_grillas.json")
    parser.add_argument("--max-columnas", type=int, default=7)
    return parser.parse_args()


def limpiar_prompt(texto: str) -> str:
    texto = re.sub(
        r"\s*Natural light, realistic professional horizontal 16:9 composition; "
        r"no readable text, logos, insignia or watermark\.?\s*$",
        "",
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(r"^Documentary photograph in Bolivia:\s*", "", texto, flags=re.IGNORECASE)
    return " ".join(texto.split()).strip().rstrip(".") + "."


def prompt_grilla(tema: int, paneles: list[dict], columnas: int) -> str:
    capacidad = columnas * 2
    hay_uniforme = any(bool(p.get("requiere_uniforme")) for p in paneles)
    partes = [
        f"Create ONE horizontal 16:9 contact sheet made of exactly {capacidad} equal rectangular cells arranged in a strict {columnas}-column by 2-row grid, read left-to-right then top-to-bottom.",
        "Use thin clean white gutters. Every occupied cell must contain one different realistic professional documentary photograph; no illustration, icons, split scenes inside a cell, cinematic grading, HDR, captions, words, numbers, letters, logos, licence plates, badges, coats of arms, borders around the entire sheet, or watermarks.",
        "All occupied cells must look like genuine photographs taken in Bolivia, using natural high-altitude light, ordinary imperfect public interiors or unmistakable La Paz and El Alto streets with steep dry Andean red-brick hills. Use adult people only; correct faces, hands, vehicles and anatomy; never duplicate a person or scene.",
        "Keep each subject centered with vertical-friendly framing. Do not add police to a cell unless its numbered description explicitly mentions police or a police officer.",
    ]
    if hay_uniforme:
        partes.append(
            "Where a numbered description includes Bolivian police, match the supplied real reference: adult officers in very dark olive-green shirt-jacket and matching trousers, olive baseball cap, black service boots and belt, and when operationally appropriate a fluorescent lime-green vest with two silver reflective bands. Professional non-aggressive posture. All crest, badge, rank and lettering areas remain plain unmarked fabric; no weapons."
        )
    if any(bool(p.get("sensible")) for p in paneles):
        partes.append(
            "For sensitive subjects show only lawful procedure, prevention, an institutional object or a dignified consequence; never depict torture, abuse, injury, blood, bribery in progress, humiliation or physical confrontation."
        )
    partes.append("Numbered cell descriptions:")
    for indice, panel in enumerate(paneles, 1):
        marca = "This cell includes Bolivian police. " if panel.get("requiere_uniforme") else "No police in this cell. "
        partes.append(f"{indice}) {marca}{limpiar_prompt(panel['prompt'])}")
    if len(paneles) < capacidad:
        for indice in range(len(paneles) + 1, capacidad + 1):
            partes.append(f"{indice}) EMPTY CELL: pure white, no photograph and no marks.")
    partes.append(
        f"Critical layout check: exactly {columnas} columns and exactly 2 rows, exactly {len(paneles)} occupied photographs in the numbered order"
        + (f", followed by {capacidad - len(paneles)} pure-white empty cell." if capacidad > len(paneles) else ".")
    )
    return " ".join(partes)


def main() -> int:
    args = argumentos()
    trabajos = []
    maximo = args.max_columnas * 2
    for plan in sorted(args.planes):
        data = json.loads(plan.read_text(encoding="utf-8"))
        tema = int(data["tema"])
        hojas = partir_por_diapositiva(data["paneles"], maximo)
        for numero, paneles in enumerate(hojas, 1):
            columnas = math.ceil(len(paneles) / 2)
            trabajos.append({
                "id": f"tema{tema:02d}_grilla_{numero:02d}",
                "tema": tema,
                "lamina": numero,
                "columnas": columnas,
                "filas": 2,
                "paneles": [p["id"] for p in paneles],
                "rotulos": [p["rotulo"] for p in paneles],
                "requiere_uniforme": any(bool(p.get("requiere_uniforme")) for p in paneles),
                "perfil_referencia": "formal" if tema in {13, 14} else "operativo",
                "prompt": prompt_grilla(tema, paneles, columnas),
                "destino": str(
                    ROOT / "paneles" / "grillas_brutas" / f"tema{tema:02d}" /
                    f"tema{tema:02d}_grilla_{numero:02d}.png"
                ),
            })
    payload = {
        "formato": "contact sheet 16:9, columnas variables x 2 filas",
        "trabajos": trabajos,
        "total_grillas": len(trabajos),
        "total_paneles": sum(len(t["paneles"]) for t in trabajos),
    }
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "salida": str(args.salida), "grillas": len(trabajos),
        "paneles": payload["total_paneles"],
        "por_tema": {tema: sum(1 for t in trabajos if t["tema"] == tema) for tema in range(3, 15)},
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
