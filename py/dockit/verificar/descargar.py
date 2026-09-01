#!/usr/bin/env python3
"""Descarga los PDF de acceso abierto de la biblioteca.

    sisifo descargar [--todos]

Solo baja lo que las propias APIs publican como acceso abierto (`_pdf`), y para
los que no lo traen consulta Unpaywall, que da la copia legal cuando existe.
Nada de saltarse muros de pago: lo que no es abierto se queda con su resumen y
se anota como tal.

Unpaywall exige identificarse: define TALLER_MAILTO con tu correo si quieres
usarla. Sin esa variable, se salta ese paso.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

UA = "taller-investigacion/1.0 (uso academico)"
MAILTO = os.environ.get("TALLER_MAILTO", "").strip()
MAX_MB = 60


def pdf_por_unpaywall(doi: str) -> str | None:
    if not MAILTO:
        return None
    try:
        r = requests.get(f"https://api.unpaywall.org/v2/{doi}",
                         params={"email": MAILTO}, timeout=20,
                         headers={"User-Agent": UA})
        if r.status_code != 200:
            return None
        mejor = r.json().get("best_oa_location") or {}
        return mejor.get("url_for_pdf")
    except requests.RequestException:
        return None


def bajar(url: str, destino: Path) -> tuple[bool, str]:
    try:
        r = requests.get(url, timeout=60, stream=True, allow_redirects=True,
                         headers={"User-Agent": UA})
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        tipo = r.headers.get("Content-Type", "")
        trozos, total = [], 0
        for t in r.iter_content(65536):
            trozos.append(t)
            total += len(t)
            if total > MAX_MB * 1024 * 1024:
                return False, f"pesa más de {MAX_MB} MB"
        datos = b"".join(trozos)
        if not datos.startswith(b"%PDF"):
            return False, f"no es un PDF ({tipo or 'sin tipo'})"
        destino.write_bytes(datos)
        return True, f"{total / 1024 / 1024:.1f} MB"
    except requests.RequestException as e:
        return False, f"{type(e).__name__}"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--carpeta", type=Path, required=True)
    p.add_argument("--todos", action="store_true",
                   help="intenta también los que no vienen marcados como abiertos")
    args = p.parse_args()

    biblioteca = args.carpeta / "fuentes" / "biblioteca.json"
    if not biblioteca.exists():
        sys.exit("no hay fuentes/biblioteca.json — usa 'sisifo buscar' primero")
    refs = json.loads(biblioteca.read_text())

    destino = args.carpeta / "fuentes" / "pdf"
    destino.mkdir(parents=True, exist_ok=True)

    bajados = fallidos = saltados = 0
    for e in refs:
        clave = e.get("id")
        if not clave:
            continue
        archivo = destino / f"{re.sub(r'[^a-zA-Z0-9_-]', '', clave)}.pdf"
        if archivo.exists():
            saltados += 1
            continue

        url = e.get("_pdf")
        if not url and e.get("DOI"):
            url = pdf_por_unpaywall(e["DOI"])
            time.sleep(0.2)
        if not url:
            if not args.todos:
                saltados += 1
                continue
            url = e.get("URL")
        if not url:
            saltados += 1
            continue

        ok, detalle = bajar(url, archivo)
        if ok:
            print(f"  [ ok ] {clave} — {detalle}")
            e["_pdf_local"] = str(archivo.relative_to(args.carpeta))
            bajados += 1
        else:
            print(f"  [ -- ] {clave} — {detalle}")
            fallidos += 1
        time.sleep(0.4)

    biblioteca.write_text(json.dumps(refs, ensure_ascii=False, indent=2))
    con_pdf = sum(1 for e in refs if e.get("_pdf_local"))
    print(f"\n{bajados} descargados, {fallidos} no se pudieron, {saltados} saltados")
    print(f"{con_pdf}/{len(refs)} referencias con PDF local en fuentes/pdf/")
    if not MAILTO:
        print("sugerencia: export TALLER_MAILTO=tu@correo -> Unpaywall busca más copias legales")
    print("siguiente: sisifo extraer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
