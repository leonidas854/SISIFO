#!/usr/bin/env python3
"""Expande un plan semántico a prompts finales listos para generar.

Cada trabajo del plan trae un ``prompt`` con lo específico de la diapositiva y una
lista ``bloques`` con los nombres de los bloques comunes que hay que anexar
(identidad del uniforme, entorno boliviano, estilo del registro, prohibiciones).
Este script los concatena en ``prompt_final`` y valida el plan antes de gastar GPU.

    python3 herramientas/armar_prompts.py prompts/tema03_plan.json \
        -o prompts/tema03_expandido.json

Con ``--listado`` imprime además un resumen legible por diapositiva.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
BLOQUES_POR_DEFECTO = RAIZ / "prompts" / "bloques_comunes.json"

# Registros previstos por el método: A escena documental, B paneles, C ilustración.
REGISTROS = {"A", "B", "C"}

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagramas import ARQUETIPOS, ICONS as ICONOS  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("plan", type=Path, help="Plan semántico de un tema")
    p.add_argument("-o", "--output", type=Path, help="JSON expandido de salida")
    p.add_argument("--bloques", type=Path, default=BLOQUES_POR_DEFECTO)
    p.add_argument("--listado", action="store_true", help="Resumen legible por diapositiva")
    p.add_argument("--estricto", action="store_true", help="Aborta si hay avisos")
    return p.parse_args()


def expandir(trabajo: dict, bloques: dict) -> str:
    partes = [trabajo["prompt"].strip()]
    for nombre in trabajo.get("bloques", []):
        if nombre not in bloques:
            raise KeyError(f"bloque desconocido: {nombre}")
        partes.append(bloques[nombre].strip())
    relacion = trabajo.get("relacion")
    if relacion:
        partes.append(f"Horizontal {relacion} composition.")
    return " ".join(partes)


def validar(trabajos: list[dict]) -> list[str]:
    avisos: list[str] = []
    por_diapo: dict[int, list[dict]] = defaultdict(list)
    for t in trabajos:
        por_diapo[t["diapositiva"]].append(t)

    for diapo, grupo in sorted(por_diapo.items()):
        if len(grupo) != 2:
            avisos.append(f"diapo {diapo:02d}: {len(grupo)} opciones, se esperaban 2")
        motores = [t.get("motor") for t in grupo]
        if "vector" not in motores:
            avisos.append(
                f"diapo {diapo:02d}: ninguna opción es diagrama local; "
                "cada diapositiva lleva una opción conceptual y una fotográfica"
            )
        if all(m == "vector" for m in motores):
            avisos.append(f"diapo {diapo:02d}: las dos opciones son diagrama; falta la fotográfica")
        desconocidos = {t.get("registro") for t in grupo} - REGISTROS
        if desconocidos:
            avisos.append(f"diapo {diapo:02d}: registro no previsto {sorted(desconocidos)}")
        for t in grupo:
            for campo in ("concepto_visual", "que_debe_leerse"):
                if not t.get(campo):
                    avisos.append(f"diapo {diapo:02d} op{t['opcion']}: falta {campo}")
            if t.get("motor") == "vector" and t.get("archivo_svg"):
                pass  # diagrama dibujado a mano: no lleva spec ni prompt
            elif t.get("motor") == "vector":
                if not isinstance(t.get("spec"), dict):
                    avisos.append(f"diapo {diapo:02d} op{t['opcion']}: falta el spec del diagrama")
                elif t["spec"].get("tipo") not in ARQUETIPOS:
                    avisos.append(
                        f"diapo {diapo:02d} op{t['opcion']}: arquetipo desconocido "
                        f"{t['spec'].get('tipo')!r}"
                    )
                else:
                    faltan = [i for i in t["spec"].get("iconos", []) if i not in ICONOS]
                    if faltan:
                        avisos.append(f"diapo {diapo:02d} op{t['opcion']}: iconos inexistentes {faltan}")
            elif not t.get("prompt"):
                avisos.append(f"diapo {diapo:02d} op{t['opcion']}: falta prompt")

    # Una escena repetida dentro del tema es el defecto que hundió el material anterior.
    conceptos = Counter(t.get("concepto_visual", "").lower() for t in trabajos)
    for concepto, veces in conceptos.items():
        if veces > 1:
            avisos.append(f"concepto visual repetido {veces} veces: {concepto[:70]}")

    return avisos


def main() -> int:
    args = parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    bloques = {
        k: v for k, v in json.loads(args.bloques.read_text(encoding="utf-8")).items()
        if not k.startswith("_")
    }
    trabajos = plan["trabajos"]

    avisos = validar(trabajos)
    for aviso in avisos:
        print(f"aviso: {aviso}", file=sys.stderr)
    if avisos and args.estricto:
        return 1

    for t in trabajos:
        if t.get("motor") != "vector":
            t["prompt_final"] = expandir(t, bloques)

    if args.listado:
        actual = None
        for t in sorted(trabajos, key=lambda x: (x["diapositiva"], x["opcion"])):
            if t["diapositiva"] != actual:
                actual = t["diapositiva"]
                print(f"\nDiapo {actual:02d} — {t['titulo']}")
            print(f"  op{t['opcion']} [{t['registro']}] {t['concepto_visual']}")
            print(f"       lee: {t['que_debe_leerse']}")

    salida = args.output or args.plan.with_name(args.plan.stem + "_expandido.json")
    salida.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    largos = [len(t["prompt_final"]) for t in trabajos if "prompt_final" in t]
    motores = Counter(t.get("motor") for t in trabajos)
    local = motores["vector"] + motores["sdxl"]
    print(
        f"\n{len(trabajos)} trabajos -> {salida} | "
        f"{local} locales ({motores['vector']} vector + {motores['sdxl']} sdxl), "
        f"{motores['imagegen']} imagegen"
    )
    if largos:
        print(f"prompts expandidos: {len(largos)} (min {min(largos)} / max {max(largos)} caracteres)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
