#!/usr/bin/env python3
"""Redacta el borrador del trabajo con un modelo local, anclado a las fuentes.

    redactar.py --carpeta <t> [--modelo llama3.2] [--pasajes 6] [--palabras 320]

Para cada sección del esquema: recupera del índice los pasajes pertinentes con
bge-m3, se los entrega al modelo local y le prohíbe salir de ahí. Después
filtra las citas —solo claves verificadas— y convierte cada frase con dato en
una afirmación con su cita literal, para que `sisifo datos` pueda comprobarla.

Escribe `guion.json` y `afirmaciones.json`. El modelo redacta; quien decide si
vale es el verificador y, al final, la persona.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dockit.redaccion import anclaje, limpieza, ollama, plan  # noqa: E402


def cargar(p: Path, defecto):
    if not p.exists():
        return defecto
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return defecto


def consultar_indice(carpeta: Path, pregunta: str, n: int) -> list[dict]:
    """Recupera pasajes con el índice local. Sin índice, no hay redacción:
    escribir sin fuentes es justo lo que este sistema impide."""
    r = subprocess.run(["sisifo", "consultar", pregunta, str(n)],
                       capture_output=True, text=True, cwd=str(carpeta), timeout=300)
    if r.returncode != 0:
        return []
    pasajes, fuente, buffer = [], None, []
    for linea in r.stdout.splitlines():
        if linea.startswith("── "):
            if fuente and buffer:
                pasajes.append({"fuente": fuente, "texto": " ".join(buffer).strip()})
            fuente, buffer = linea[3:].split("  (")[0].strip(), []
        elif fuente and linea.strip() and not linea.startswith("Cita SOLO"):
            buffer.append(linea.strip())
    if fuente and buffer:
        pasajes.append({"fuente": fuente, "texto": " ".join(buffer).strip()})
    return pasajes


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--carpeta", type=Path, required=True)
    p.add_argument("--modelo", default="llama3.2")
    p.add_argument("--pasajes", type=int, default=6)
    p.add_argument("--palabras", type=int, default=320)
    p.add_argument("--titulo", default="")
    p.add_argument("--vinetas", type=int, default=5,
                   help="viñetas por diapositiva (más de cinco no se leen)")
    args = p.parse_args()

    carpeta = args.carpeta.resolve()
    if not ollama.disponible(args.modelo):
        sys.exit(f"no encuentro el modelo «{args.modelo}» en ollama "
                 f"(ollama pull {args.modelo})")
    if not (carpeta / "fuentes" / "indice.gob").exists():
        sys.exit("no hay índice — ejecuta 'sisifo indexar' antes")

    en_texto = cargar(carpeta / "fuentes" / "citas_en_texto.json", {})
    verificadas = set(en_texto)
    if not verificadas:
        sys.exit("no hay referencias verificadas — ejecuta 'sisifo bib --verificar'")

    titulo = args.titulo or carpeta.name.replace("_", " ").replace("-", " ").capitalize()
    secciones = plan.esquema_por_defecto(titulo)

    print(f"redactando {len(secciones)} secciones con {args.modelo}")
    print(f"{len(verificadas)} referencias verificadas disponibles\n")

    bloques: list[dict] = [
        {"clase": "indice"},
        {"clase": "indice_tablas"},
        {"clase": "indice_figuras"},
    ]
    afirmaciones: list[dict] = []
    descartadas_total: list[str] = []
    para_diapos: list[dict] = []

    for i, sec in enumerate(secciones, 1):
        pregunta = f"{titulo}: {sec['titulo']}. {sec['proposito']}"
        pasajes = consultar_indice(carpeta, pregunta, args.pasajes)
        if not pasajes:
            print(f"  [{i}/{len(secciones)}] {sec['titulo']}: sin pasajes, se omite")
            continue

        texto = ollama.generar(
            plan.prompt_seccion(sec["titulo"], sec["proposito"], pasajes,
                                "es", args.palabras),
            modelo=args.modelo, maximo=int(args.palabras * 2.2))

        # 1. fuera las claves que el modelo se inventó
        texto, descartadas = anclaje.filtrar_citas(texto, verificadas)
        descartadas_total += descartadas

        # 2. fuera las claves buenas del cuerpo: la cita definitiva la pone
        #    citeproc, y así el año de la clave no se confunde con un dato
        limpio, citadas = anclaje.normalizar_citas(texto, verificadas)
        limpio = limpieza.sin_marcadores_numericos(
            limpieza.sin_restos_de_cita(limpio))

        # 3. lo que quede con cifras, a verificar contra los pasajes
        nuevas = anclaje.extraer_afirmaciones(
            limpio, pasajes, verificadas, prefijo=f"s{i}_")
        afirmaciones += nuevas
        limpio = " ".join(limpio.split())

        bloques.append({"clase": "titulo", "nivel": 1, "texto": sec["titulo"]})
        bloques.append({"clase": "parrafo", "texto": limpio, "citas": citadas})

        # las diapositivas no repiten el informe: se quedan con lo fundamental
        vinetas = plan.vinetas_desde(
            ollama.generar(plan.prompt_lamina(sec["titulo"], limpio, args.vinetas),
                           modelo=args.modelo, maximo=260),
            maximo=args.vinetas)
        if vinetas:
            para_diapos.append({"titulo": sec["titulo"], "vinetas": vinetas})
        print(f"  [{i}/{len(secciones)}] {sec['titulo']}: "
              f"{len(limpio.split())} palabras · {len(citadas)} citas · "
              f"{len(nuevas)} afirmaciones")

    bloques.append({"clase": "bibliografia"})

    guion = {"tipo": "docx", "titulo": titulo,
             "autor": "", "bloques": bloques}
    (carpeta / "guion.json").write_text(
        json.dumps(guion, ensure_ascii=False, indent=2), encoding="utf-8")
    (carpeta / "afirmaciones.json").write_text(
        json.dumps(afirmaciones, ensure_ascii=False, indent=2), encoding="utf-8")

    diapos = plan.guion_diapositivas(titulo, para_diapos)
    (carpeta / "guion_diapos.json").write_text(
        json.dumps(diapos, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nguion.json: {len(bloques)} bloques")
    print(f"guion_diapos.json: {len(para_diapos)} láminas, "
          f"una por sección del índice")
    print(f"afirmaciones.json: {len(afirmaciones)} afirmaciones que verificar")
    if descartadas_total:
        # se cuentan por identidad, no por grafía: Egberts2017 y egberts2017
        # son la misma clave inventada escrita de dos maneras
        unicas = sorted({c.lower() for c in descartadas_total})
        print(f"{len(unicas)} clave(s) inventadas por el modelo, "
              f"descartadas: {', '.join(unicas[:4])}")
    print("\nsiguiente: sisifo datos   (comprueba que cada dato tenga respaldo)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
