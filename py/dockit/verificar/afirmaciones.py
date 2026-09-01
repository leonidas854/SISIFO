#!/usr/bin/env python3
"""Comprueba que cada afirmación del trabajo salga de una fuente real.

    # 1. extraer el texto de los PDF que hay en fuentes/
    sisifo extraer

    # 2. verificar afirmaciones.json contra ese texto
    sisifo datos

Cada entrada de `afirmaciones.json` declara qué se afirma, de qué fuente sale y
con qué cita literal. La cita tiene que APARECER en el texto de la fuente. Una
afirmación inventada no puede pasar: su cita no está en ningún documento.

    [{"id": "a1",
      "texto": "La cadena de custodia documenta cada transferencia.",
      "fuente": "nath2024digital",
      "cita": "chain of custody documents every transfer",
      "localizador": "p. 12"}]
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

UMBRAL = 0.90          # por debajo de esto, la cita no se considera hallada
VENTANA_EXTRA = 60     # margen al buscar la mejor ventana del texto


def normalizar(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = s.encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", s)).strip()


# ── extracción de texto ───────────────────────────────────────────────────

def extraer_pdf(ruta: Path) -> str:
    """pdftotext primero (rápido y fiel al layout); pypdf de respaldo."""
    try:
        r = subprocess.run(["pdftotext", "-q", str(ruta), "-"],
                           capture_output=True, timeout=120)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.decode("utf-8", "replace")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(ruta)).pages)
    except Exception as e:
        print(f"    no pude leer {ruta.name}: {e}", file=sys.stderr)
        return ""


def extraer(carpeta: Path) -> int:
    fuentes = carpeta / "fuentes"
    destino = fuentes / "textos"
    destino.mkdir(parents=True, exist_ok=True)
    docs = [p for p in fuentes.rglob("*")
            if p.suffix.lower() in {".pdf", ".txt", ".md"}
            and destino not in p.parents]
    if not docs:
        print(f"no hay PDF ni TXT en {fuentes}/")
        return 0

    n = 0
    for doc in sorted(docs):
        salida = destino / (doc.stem + ".txt")
        if salida.exists() and salida.stat().st_mtime > doc.stat().st_mtime:
            continue
        texto = (extraer_pdf(doc) if doc.suffix.lower() == ".pdf"
                 else doc.read_text(encoding="utf-8", errors="replace"))
        if texto.strip():
            salida.write_text(texto, encoding="utf-8")
            print(f"  {doc.name} -> textos/{salida.name} "
                  f"({len(texto.split()):,} palabras)")
            n += 1
    print(f"\n{n} documento(s) extraído(s) en fuentes/textos/")
    return n


# ── búsqueda de la cita ───────────────────────────────────────────────────

def buscar_cita(cita: str, texto: str) -> tuple[bool, float, str]:
    """¿Aparece la cita en el texto? Devuelve (hallada, parecido, contexto)."""
    c, t = normalizar(cita), normalizar(texto)
    if not c:
        return False, 0.0, ""
    if c in t:
        i = t.index(c)
        return True, 1.0, t[max(0, i - 40):i + len(c) + 40]

    # no está literal: busca la ventana más parecida
    paso = max(len(c) // 2, 25)
    mejor, mejor_pos = 0.0, 0
    for i in range(0, max(len(t) - len(c), 1), paso):
        ventana = t[i:i + len(c) + VENTANA_EXTRA]
        r = difflib.SequenceMatcher(None, c, ventana).ratio()
        if r > mejor:
            mejor, mejor_pos = r, i
    ctx = t[mejor_pos:mejor_pos + len(c) + VENTANA_EXTRA]
    return mejor >= UMBRAL, mejor, ctx


def cargar_textos(carpeta: Path) -> dict[str, str]:
    d = carpeta / "fuentes" / "textos"
    return {p.stem: p.read_text(encoding="utf-8", errors="replace")
            for p in d.glob("*.txt")} if d.exists() else {}


def texto_de_fuente(clave: str, textos: dict[str, str],
                    biblioteca: dict[str, dict]) -> tuple[str, str]:
    """Texto completo si lo hay; si no, el resumen del registro."""
    if clave in textos:
        return textos[clave], "texto completo"
    for nombre, contenido in textos.items():
        if clave.lower() in nombre.lower() or nombre.lower() in clave.lower():
            return contenido, f"texto completo ({nombre})"
    resumen = (biblioteca.get(clave) or {}).get("abstract")
    if resumen:
        return resumen, "solo el resumen"
    return "", "sin texto"


TIENE_DATO = re.compile(r"\d")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--carpeta", type=Path, required=True)
    p.add_argument("--extraer", action="store_true",
                   help="extrae texto de los PDF de fuentes/ y termina")
    args = p.parse_args()

    if args.extraer:
        extraer(args.carpeta)
        return 0

    ruta = args.carpeta / "afirmaciones.json"
    if not ruta.exists():
        print(f"no hay {ruta}.\nCrea ahí las afirmaciones con dato del trabajo, "
              f"una por objeto:\n"
              f'  [{{"id":"a1","texto":"...","fuente":"clave","cita":"cita literal"}}]')
        return 1

    afirmaciones = json.loads(ruta.read_text())
    bib_path = args.carpeta / "fuentes" / "biblioteca.json"
    biblioteca = {e["id"]: e for e in json.loads(bib_path.read_text())} \
        if bib_path.exists() else {}
    textos = cargar_textos(args.carpeta)

    fallos = avisos = 0
    print(f"{len(afirmaciones)} afirmaciones · {len(biblioteca)} referencias · "
          f"{len(textos)} documentos con texto\n")

    for a in afirmaciones:
        ident = a.get("id", "?")
        clave = a.get("fuente")
        etiqueta = f"{ident}"

        if not clave:
            estado = "SIN FUENTE" if TIENE_DATO.search(a.get("texto", "")) else "sin fuente"
            print(f"[{estado:^12}] {etiqueta}: «{a.get('texto','')[:60]}»")
            if TIENE_DATO.search(a.get("texto", "")):
                print("               lleva una cifra y no dice de dónde sale")
                fallos += 1
            else:
                avisos += 1
            continue

        if clave not in biblioteca:
            print(f"[{'NO EN BIB':^12}] {etiqueta}: la fuente «{clave}» no está "
                  f"en biblioteca.json")
            fallos += 1
            continue

        if not a.get("cita"):
            print(f"[{'SIN CITA':^12}] {etiqueta}: declara fuente pero no la cita "
                  f"literal que la respalda")
            fallos += 1
            continue

        texto, origen = texto_de_fuente(clave, textos, biblioteca)
        if not texto:
            print(f"[{'SIN TEXTO':^12}] {etiqueta}: no tengo el documento de "
                  f"«{clave}» para comprobar la cita")
            avisos += 1
            continue

        hallada, parecido, contexto = buscar_cita(a["cita"], texto)
        if hallada and parecido == 1.0:
            print(f"[{'ok':^12}] {etiqueta}: literal en {clave} ({origen})")
        elif hallada:
            print(f"[{'ok~':^12}] {etiqueta}: en {clave} con variación menor "
                  f"({parecido:.0%})")
        else:
            print(f"[{'NO ESTÁ':^12}] {etiqueta}: la cita NO aparece en {clave} "
                  f"({origen}, mejor coincidencia {parecido:.0%})")
            print(f"               cita: «{a['cita'][:70]}»")
            if contexto:
                print(f"               lo más parecido: «{contexto[:70]}»")
            fallos += 1

    print(f"\n{fallos} sin respaldo, {avisos} por revisar, "
          f"{len(afirmaciones) - fallos - avisos} verificadas")
    if fallos:
        print("Hay afirmaciones que no salen de ninguna fuente. No se entrega así.")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
