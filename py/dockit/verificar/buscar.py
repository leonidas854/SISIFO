#!/usr/bin/env python3
"""Busca en fuentes académicas reales y guarda los registros en CSL-JSON.

    sisifo buscar "cadena de custodia digital" \
            --carpeta <trabajo> --fuentes openalex,crossref --n 25

Nada de esto lo inventa un modelo: cada registro viene de una API pública con
su DOI o su identificador permanente. Lo que no trae identificador, no entra.

Variable opcional TALLER_MAILTO: tu correo. Algunas APIs dan cola preferente a
quien se identifica (OpenAlex, Crossref) y Unpaywall directamente lo exige.
Se envía SOLO si tú la defines; por defecto no se manda a ningún sitio.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

UA = "taller-investigacion/1.0 (uso academico)"
MAILTO = os.environ.get("TALLER_MAILTO", "").strip()
TIMEOUT = 20


def pedir(url: str, params: dict | None = None, xml: bool = False):
    r = requests.get(url, params=params, timeout=TIMEOUT,
                     headers={"User-Agent": UA, "Accept":
                              "application/xml" if xml else "application/json"})
    r.raise_for_status()
    return r.text if xml else r.json()


# ── normalización a CSL-JSON ──────────────────────────────────────────────

def persona(nombre_completo: str) -> dict:
    partes = (nombre_completo or "").strip().split()
    if not partes:
        return {"literal": "Anónimo"}
    return {"family": partes[-1], "given": " ".join(partes[:-1])}


MESES = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}


def _num(v) -> int | None:
    """Acepta 2024, "2024" y "December". Lo que no reconoce, lo descarta."""
    if v is None:
        return None
    if isinstance(v, int):
        return v
    v = str(v).strip()
    if v.isdigit():
        return int(v)
    return MESES.get(v.lower())


def fecha(anio, mes=None, dia=None) -> dict | None:
    a = _num(anio)
    if not a:
        return None
    partes = [a]
    m = _num(mes)
    if m:
        partes.append(m)
        d = _num(dia)
        if d:
            partes.append(d)
    return {"date-parts": [partes]}


def clave(entrada: dict) -> str:
    """apellido2020palabra — estable y legible en el texto."""
    autores = entrada.get("author") or []
    ape = (autores[0].get("family") if autores else "") or "anon"
    partes = ((entrada.get("issued") or {}).get("date-parts") or [[]])[0]
    anio = str(partes[0]) if partes else "sf"
    titulo = entrada.get("title") or ""
    palabra = next((p for p in re.findall(r"\w{4,}", titulo.lower())), "obra")
    crudo = f"{ape}{anio}{palabra}"
    crudo = unicodedata.normalize("NFKD", crudo).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", crudo.lower())


# ── fuentes ───────────────────────────────────────────────────────────────

def de_openalex(q: str, n: int, idioma: str | None) -> list[dict]:
    params = {"search": q, "per-page": min(n, 50)}
    if idioma:
        params["filter"] = f"language:{idioma}"
    if MAILTO:
        params["mailto"] = MAILTO
    datos = pedir("https://api.openalex.org/works", params)
    salida = []
    for w in datos.get("results", []):
        loc = (w.get("primary_location") or {}).get("source") or {}
        salida.append({
            "type": "article-journal",
            "title": w.get("title") or "",
            "author": [persona(a["author"]["display_name"])
                       for a in (w.get("authorships") or [])[:15]
                       if a.get("author", {}).get("display_name")],
            "issued": fecha(w.get("publication_year")),
            "container-title": loc.get("display_name"),
            "DOI": (w.get("doi") or "").replace("https://doi.org/", "") or None,
            "URL": w.get("doi") or w.get("id"),
            "abstract": reconstruir_resumen(w.get("abstract_inverted_index")),
            "_fuente": "openalex",
            "_acceso_abierto": (w.get("open_access") or {}).get("is_oa"),
            "_pdf": (w.get("best_oa_location") or {}).get("pdf_url"),
            "_citado_por": w.get("cited_by_count"),
        })
    return salida


def reconstruir_resumen(indice: dict | None) -> str | None:
    """OpenAlex guarda el resumen como índice invertido; se rearma."""
    if not indice:
        return None
    posiciones: list[tuple[int, str]] = []
    for palabra, ocurrencias in indice.items():
        posiciones += [(p, palabra) for p in ocurrencias]
    return " ".join(w for _, w in sorted(posiciones))[:2000] or None


def fecha_crossref(issued) -> dict | None:
    partes = ((issued or {}).get("date-parts") or [[]])[0] or []
    return fecha(*(list(partes) + [None, None])[:3])


def de_crossref(q: str, n: int, idioma: str | None) -> list[dict]:
    params = {"query": q, "rows": min(n, 50), "select":
              "DOI,title,author,issued,container-title,volume,issue,page,type,publisher,abstract"}
    if MAILTO:
        params["mailto"] = MAILTO
    datos = pedir("https://api.crossref.org/works", params)
    salida = []
    for w in datos.get("message", {}).get("items", []):
        salida.append({
            "type": "article-journal" if w.get("type") == "journal-article" else "document",
            "title": (w.get("title") or [""])[0],
            "author": [{"family": a.get("family", ""), "given": a.get("given", "")}
                       for a in (w.get("author") or [])[:15] if a.get("family")],
            "issued": fecha_crossref(w.get("issued")),
            "container-title": (w.get("container-title") or [None])[0],
            "volume": w.get("volume"), "issue": w.get("issue"), "page": w.get("page"),
            "publisher": w.get("publisher"),
            "DOI": w.get("DOI"),
            "URL": f"https://doi.org/{w['DOI']}" if w.get("DOI") else None,
            "abstract": re.sub(r"<[^>]+>", "", w.get("abstract") or "") or None,
            "_fuente": "crossref",
        })
    return salida


def de_doaj(q: str, n: int, idioma: str | None) -> list[dict]:
    datos = pedir(f"https://doaj.org/api/search/articles/{urllib.parse.quote(q)}",
                  {"pageSize": min(n, 50)})
    salida = []
    for it in datos.get("results", []):
        b = it.get("bibjson", {})
        doi = next((i["id"] for i in b.get("identifier", []) if i.get("type") == "doi"), None)
        salida.append({
            "type": "article-journal",
            "title": b.get("title") or "",
            "author": [persona(a.get("name", "")) for a in b.get("author", [])[:15]],
            "issued": fecha(b.get("year"), b.get("month")),
            "container-title": (b.get("journal") or {}).get("title"),
            "volume": (b.get("journal") or {}).get("volume"),
            "DOI": doi,
            "URL": next((l["url"] for l in b.get("link", []) if l.get("url")), None),
            "abstract": b.get("abstract"),
            "_fuente": "doaj", "_acceso_abierto": True,
        })
    return salida


def de_arxiv(q: str, n: int, idioma: str | None) -> list[dict]:
    txt = pedir("https://export.arxiv.org/api/query",
                {"search_query": f"all:{q}", "max_results": min(n, 50)}, xml=True)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    salida = []
    for e in ET.fromstring(txt).findall("a:entry", ns):
        pub = (e.findtext("a:published", "", ns) or "")[:10].split("-")
        ident = e.findtext("a:id", "", ns)
        salida.append({
            "type": "article",
            "title": " ".join((e.findtext("a:title", "", ns) or "").split()),
            "author": [persona(a.findtext("a:name", "", ns))
                       for a in e.findall("a:author", ns)[:15]],
            "issued": fecha(*pub) if pub and pub[0] else None,
            "container-title": "arXiv",
            "DOI": e.findtext("a:doi", None, ns),
            "URL": ident,
            "abstract": " ".join((e.findtext("a:summary", "", ns) or "").split()),
            "_fuente": "arxiv", "_acceso_abierto": True,
            "_pdf": ident.replace("/abs/", "/pdf/") if ident else None,
        })
    return salida


def de_europepmc(q: str, n: int, idioma: str | None) -> list[dict]:
    datos = pedir("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                  {"query": q, "format": "json", "pageSize": min(n, 50),
                   "resultType": "core"})
    salida = []
    for w in datos.get("resultList", {}).get("result", []):
        salida.append({
            "type": "article-journal",
            "title": w.get("title") or "",
            "author": [persona(a.get("fullName", ""))
                       for a in (w.get("authorList") or {}).get("author", [])[:15]],
            "issued": fecha(w.get("pubYear")),
            "container-title": w.get("journalTitle"),
            "volume": w.get("journalVolume"), "page": w.get("pageInfo"),
            "DOI": w.get("doi"),
            "URL": f"https://doi.org/{w['doi']}" if w.get("doi") else None,
            "abstract": w.get("abstractText"),
            "_fuente": "europepmc",
            "_acceso_abierto": w.get("isOpenAccess") == "Y",
        })
    return salida


FUENTES = {"openalex": de_openalex, "crossref": de_crossref, "doaj": de_doaj,
           "arxiv": de_arxiv, "europepmc": de_europepmc}


# ── unión y guardado ──────────────────────────────────────────────────────

def normalizar_titulo(t: str) -> str:
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return re.sub(r"[^a-z0-9]", "", t.encode("ascii", "ignore").decode())


def fundir(existentes: list[dict], nuevos: list[dict]) -> tuple[list[dict], int]:
    por_doi = {e["DOI"].lower() for e in existentes if e.get("DOI")}
    por_tit = {normalizar_titulo(e.get("title", "")) for e in existentes}
    claves = {e["id"] for e in existentes if e.get("id")}
    agregados = 0

    for e in nuevos:
        if not e.get("title"):
            continue
        doi = (e.get("DOI") or "").lower()
        tit = normalizar_titulo(e["title"])
        if (doi and doi in por_doi) or tit in por_tit:
            continue
        base = clave(e)
        k, i = base, 1
        while k in claves:
            i += 1
            k = f"{base}{chr(96 + i)}"
        e["id"] = k
        claves.add(k)
        if doi:
            por_doi.add(doi)
        por_tit.add(tit)
        existentes.append(e)
        agregados += 1
    return existentes, agregados


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("consulta")
    p.add_argument("--carpeta", type=Path, required=True)
    p.add_argument("--fuentes", default="openalex,crossref")
    p.add_argument("--n", type=int, default=25)
    p.add_argument("--idioma", help="filtro de idioma en OpenAlex, ej. es")
    args = p.parse_args()

    biblioteca = args.carpeta / "fuentes" / "biblioteca.json"
    biblioteca.parent.mkdir(parents=True, exist_ok=True)
    existentes = json.loads(biblioteca.read_text()) if biblioteca.exists() else []

    pedidas = [f.strip() for f in args.fuentes.split(",") if f.strip()]
    desconocidas = [f for f in pedidas if f not in FUENTES]
    if desconocidas:
        sys.exit(f"fuente desconocida: {', '.join(desconocidas)}. "
                 f"Disponibles: {', '.join(FUENTES)}")

    for nombre in pedidas:
        try:
            hallados = FUENTES[nombre](args.consulta, args.n, args.idioma)
            existentes, nuevos = fundir(existentes, hallados)
            print(f"  {nombre:<12} {len(hallados):>3} encontrados, {nuevos:>3} nuevos")
        except Exception as e:
            print(f"  {nombre:<12} ERROR {type(e).__name__}: {e}", file=sys.stderr)
        time.sleep(0.4)

    biblioteca.write_text(json.dumps(existentes, ensure_ascii=False, indent=2))

    # registro de la estrategia de búsqueda: sin esto la revisión no es
    # reproducible y no se puede declarar el método en el trabajo
    registro = biblioteca.parent / "busquedas.json"
    hechas = json.loads(registro.read_text()) if registro.exists() else []
    hechas.append({
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "consulta": args.consulta,
        "fuentes": pedidas,
        "idioma": args.idioma,
        "pedidos_por_fuente": args.n,
        "total_tras_la_busqueda": len(existentes),
    })
    registro.write_text(json.dumps(hechas, ensure_ascii=False, indent=2))

    con_doi = sum(1 for e in existentes if e.get("DOI"))
    print(f"\n{biblioteca.relative_to(args.carpeta)}: {len(existentes)} registros "
          f"({con_doi} con DOI)")
    if not MAILTO:
        print("sugerencia: export TALLER_MAILTO=tu@correo  -> cola preferente y Unpaywall")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
