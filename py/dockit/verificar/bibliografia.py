#!/usr/bin/env python3
"""Verifica que cada referencia EXISTE y la formatea en APA 7.

    _taller/.venv/bin/python _taller/bin/bibliografia.py --carpeta <trabajo> \
        [--verificar] [--locale es-ES] [--salida salida/bibliografia.md]

--verificar consulta cada DOI contra Crossref: si el DOI no resuelve, o el
título registrado no se parece al que tenemos, se marca. Una referencia
inventada no sobrevive a esto, porque su DOI simplemente no existe.

El formato APA lo produce citeproc-py con el estilo oficial CSL, no un modelo:
mismo registro, misma salida, siempre.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests
from citeproc import (Citation, CitationItem, CitationStylesBibliography,
                      CitationStylesStyle, formatter)
from citeproc.source.json import CiteProcJSON
from citeproc_styles import get_style_filepath

UA = "taller-investigacion/1.0 (uso academico)"

CAMPOS_CSL = {
    "id", "type", "title", "author", "editor", "issued", "accessed",
    "container-title", "collection-title", "publisher", "publisher-place",
    "volume", "issue", "page", "DOI", "URL", "ISBN", "ISSN", "edition",
    "abstract", "language", "note", "number", "genre", "event", "medium",
}


def limpiar(entrada: dict) -> dict:
    """Quita los campos internos (_fuente, _pdf…) que CSL no entiende."""
    return {k: v for k, v in entrada.items() if k in CAMPOS_CSL and v is not None}


def parecido(a: str, b: str) -> float:
    def norm(s):
        s = unicodedata.normalize("NFKD", (s or "").lower())
        s = s.encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9 ]", " ", s).split()
    return difflib.SequenceMatcher(None, " ".join(norm(a)), " ".join(norm(b))).ratio()


# ── verificación contra Crossref ──────────────────────────────────────────

def titulo_en_crossref(doi: str) -> tuple[str | None, str]:
    r = requests.get(f"https://api.crossref.org/works/{doi}", timeout=20,
                     headers={"User-Agent": UA})
    if r.status_code == 404:
        return None, "404"
    r.raise_for_status()
    return (r.json().get("message", {}).get("title") or [""])[0], "ok"


def titulo_en_datacite(doi: str) -> tuple[str | None, str]:
    """Muchos DOI legítimos (Dagstuhl, Zenodo, repositorios) no están en
    Crossref sino en DataCite. Sin esta segunda consulta se marcarían como
    inventados fuentes que son perfectamente reales."""
    r = requests.get(f"https://api.datacite.org/dois/{doi}", timeout=20,
                     headers={"User-Agent": UA})
    if r.status_code == 404:
        return None, "404"
    r.raise_for_status()
    attrs = r.json().get("data", {}).get("attributes", {})
    return (attrs.get("titles") or [{}])[0].get("title"), "ok"


def verificar(entradas: list[dict]) -> list[tuple[dict, str, str]]:
    """Devuelve (entrada, estado, detalle) por cada registro."""
    informe = []
    for e in entradas:
        doi = e.get("DOI")
        if not doi:
            informe.append((e, "SIN-DOI",
                            "no tiene DOI; verifícala a mano antes de citarla"))
            continue

        titulo_real, registro = None, None
        try:
            for nombre, consulta in (("Crossref", titulo_en_crossref),
                                     ("DataCite", titulo_en_datacite)):
                titulo_real, estado = consulta(doi)
                if estado == "ok":
                    registro = nombre
                    break
                time.sleep(0.15)
        except requests.RequestException as exc:
            informe.append((e, "ERROR", f"no pude consultar: {exc}"))
            continue

        if registro is None:
            informe.append((e, "NO EXISTE",
                            f"ni Crossref ni DataCite conocen el DOI {doi}"))
            continue

        sim = parecido(e.get("title", ""), titulo_real or "")
        if sim < 0.60:
            informe.append((e, "NO COINCIDE",
                            f"el DOI existe en {registro} pero es "
                            f"«{(titulo_real or '')[:55]}»"))
        else:
            informe.append((e, "ok", f"{registro}: {(titulo_real or '')[:50]}"))
        time.sleep(0.15)
    return informe


# ── formato APA 7 ─────────────────────────────────────────────────────────

def formatear(entradas: list[dict], locale: str
              ) -> tuple[list[str], dict[str, str], dict[str, str]]:
    """Devuelve (referencias, {clave: cita en texto}, {clave: entrada APA})."""
    limpias = [limpiar(e) for e in entradas if e.get("id")]
    fuente = CiteProcJSON(limpias)
    estilo = CitationStylesStyle(get_style_filepath("apa"), locale=locale,
                                 validate=False)
    bib = CitationStylesBibliography(estilo, fuente, formatter.plain)
    citas = {clave: Citation([CitationItem(clave)]) for clave in fuente}
    for c in citas.values():
        bib.register(c)
    referencias = [str(x) for x in bib.bibliography()]
    # el mapa clave -> entrada, para que quien produzca el documento no tenga
    # que adivinar qué entrada corresponde a qué cita
    por_clave = dict(zip(fuente, referencias))
    # la cita en el texto tiene que salir del mismo motor que la referencia,
    # o el "et al." y el orden de autores se desincronizan
    en_texto = {k: str(bib.cite(c, lambda _: None)) for k, c in citas.items()}
    return referencias, en_texto, por_clave


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--carpeta", type=Path, required=True)
    p.add_argument("--verificar", action="store_true")
    p.add_argument("--locale", default="es-ES", help="es-ES | en-US")
    p.add_argument("--salida", default="salida/bibliografia.md")
    args = p.parse_args()

    biblioteca = args.carpeta / "fuentes" / "biblioteca.json"
    if not biblioteca.exists():
        sys.exit(f"no hay {biblioteca} — usa buscar.py primero")
    entradas = json.loads(biblioteca.read_text())
    if not entradas:
        sys.exit("la biblioteca está vacía")

    usables = entradas
    if args.verificar:
        print(f"verificando {len(entradas)} referencias contra Crossref...\n")
        informe = verificar(entradas)
        malas = []
        for e, estado, detalle in informe:
            if estado == "ok":
                continue
            malas.append(e.get("id"))
            print(f"[{estado:^11}] {e.get('id')}: {detalle}")
        buenas = len(informe) - len(malas)
        print(f"\n{buenas}/{len(informe)} verificadas contra Crossref")
        if malas:
            print(f"{len(malas)} necesitan revisión tuya antes de citarse")
        # las no verificables no se tiran: se marcan y se separan
        usables = [e for e in entradas if e.get("id") not in malas]

    lineas, en_texto, por_clave = formatear(usables, args.locale)
    destino = args.carpeta / args.salida
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        "# Referencias\n\n" + "\n\n".join(sorted(lineas)) + "\n",
        encoding="utf-8")

    # el mapa clave -> "(Autor, año)" para citar dentro del texto
    mapa = args.carpeta / "fuentes" / "citas_en_texto.json"
    mapa.write_text(json.dumps(en_texto, ensure_ascii=False, indent=2),
                    encoding="utf-8")

    (args.carpeta / "fuentes" / "referencias_apa.json").write_text(
        json.dumps(por_clave, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{destino.relative_to(args.carpeta)}: {len(lineas)} referencias en APA 7")
    print(f"{mapa.relative_to(args.carpeta)}: cómo citar cada una dentro del texto")
    for k in list(en_texto)[:3]:
        print(f"  · {k} -> {en_texto[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
