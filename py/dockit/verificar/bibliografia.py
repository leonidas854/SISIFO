#!/usr/bin/env python3
"""Verifica que cada referencia EXISTE y la formatea en APA 7.

    sisifo bib [--verificar] [--locale es-ES] [--salida salida/bibliografia.md]

--verificar consulta cada DOI contra Crossref: si el DOI no resuelve, o el
título registrado no se parece al que tenemos, se marca. Una referencia
inventada no sobrevive a esto, porque su DOI simplemente no existe.

El formato APA lo produce citeproc-py con el estilo oficial CSL, no un modelo:
mismo registro, misma salida, siempre.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
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

ARCHIVO_CONFIRMACIONES = "confirmaciones_manuales.json"
ARCHIVO_MANIFIESTO = "manifiesto_verificacion.json"

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


def fecha_utc() -> str:
    """Fecha estable y legible para el rastro de auditoría."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z")


def normalizar_doi(doi: object) -> str:
    """Acepta las formas habituales sin cambiar qué DOI se comprueba."""
    valor = str(doi or "").strip()
    valor = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", valor, flags=re.I)
    valor = re.sub(r"^doi:\s*", "", valor, flags=re.I)
    return valor.strip()


def cargar_confirmaciones(ruta: Path) -> dict[str, dict]:
    """Lee confirmaciones humanas explícitas de obras que no tienen DOI.

    El formato recomendado es un objeto por clave::

        {
          "constitucion2009": {
            "confirmada": true,
            "detalle": "cotejada con la Gaceta Oficial",
            "fecha": "2026-08-31",
            "responsable": "Iniciales"
          }
        }

    También se acepta una lista de esos objetos con ``id``. La mera presencia
    de una clave no basta: debe existir una confirmación afirmativa y un detalle
    que permita saber qué se cotejó.
    """
    if not ruta.exists():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{ruta} no es JSON válido: {exc}") from exc

    if isinstance(datos, dict) and "confirmaciones" in datos:
        datos = datos["confirmaciones"]

    elementos: list[tuple[str, object]] = []
    if isinstance(datos, dict):
        elementos = [(str(clave), valor) for clave, valor in datos.items()]
    elif isinstance(datos, list):
        for valor in datos:
            if not isinstance(valor, dict) or not valor.get("id"):
                raise ValueError(
                    f"{ruta}: cada confirmación de la lista necesita un id")
            elementos.append((str(valor["id"]), valor))
    else:
        raise ValueError(f"{ruta}: se esperaba un objeto o una lista")

    confirmaciones: dict[str, dict] = {}
    for clave, valor in elementos:
        if not isinstance(valor, dict):
            raise ValueError(
                f"{ruta}: la confirmación de «{clave}» debe ser un objeto")
        estado = str(valor.get("estado") or "").strip().lower()
        afirmativa = valor.get("confirmada") is True or estado in {
            "confirmada", "confirmado", "verificada", "verificado",
        }
        detalle = str(valor.get("detalle") or "").strip()
        if not afirmativa:
            raise ValueError(
                f"{ruta}: «{clave}» necesita confirmada=true")
        if not detalle:
            raise ValueError(
                f"{ruta}: «{clave}» necesita detalle del cotejo manual")
        confirmaciones[clave] = dict(valor, id=clave, detalle=detalle)
    return confirmaciones


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


def verificar_detallado(
    entradas: list[dict],
    confirmaciones: dict[str, dict] | None = None,
    fecha: str | None = None,
) -> list[dict]:
    """Comprueba referencias y devuelve registros aptos para auditoría.

    Una confirmación manual solo se consulta cuando el registro *no declara*
    DOI. Nunca convierte en citable un DOI inexistente o perteneciente a otra
    obra.
    """
    confirmaciones = confirmaciones or {}
    comprobado_en = fecha or fecha_utc()
    ids = Counter(str(e.get("id") or "").strip() for e in entradas)
    informe: list[dict] = []

    for e in entradas:
        clave = str(e.get("id") or "").strip()
        doi = normalizar_doi(e.get("DOI"))
        base = {
            "id": clave or None,
            "estado": "",
            "registro": None,
            "detalle": "",
            "fecha": comprobado_en,
            "citable": False,
            "confirmada_manual": False,
        }
        if not clave:
            informe.append(dict(
                base,
                estado="SIN-ID",
                detalle="la referencia no tiene id y no puede citarse",
            ))
            continue
        if ids[clave] > 1:
            informe.append(dict(
                base,
                estado="ID-DUPLICADO",
                detalle=f"la clave «{clave}» aparece {ids[clave]} veces",
            ))
            continue

        if not doi:
            manual = confirmaciones.get(clave)
            if manual:
                detalle = f"confirmación manual: {manual['detalle']}"
                informe.append(dict(
                    base,
                    estado="SIN-DOI",
                    registro=str(manual.get("registro") or
                                 "confirmación manual"),
                    detalle=detalle,
                    citable=True,
                    confirmada_manual=True,
                    fecha_confirmacion=manual.get("fecha"),
                    responsable=manual.get("responsable"),
                ))
            else:
                informe.append(dict(
                    base,
                    estado="SIN-DOI",
                    detalle=("no tiene DOI; confírmala en "
                             f"fuentes/{ARCHIVO_CONFIRMACIONES} antes de citarla"),
                ))
            continue

        titulo_real, registro = None, None
        no_encontrado = 0
        errores: list[str] = []
        for nombre, consulta in (("Crossref", titulo_en_crossref),
                                 ("DataCite", titulo_en_datacite)):
            try:
                titulo_real, estado = consulta(doi)
                if estado == "ok":
                    registro = nombre
                    break
                no_encontrado += 1
            except requests.RequestException as exc:
                errores.append(f"{nombre}: {exc}")
            finally:
                time.sleep(0.15)

        if registro is None:
            if no_encontrado == 2:
                informe.append(dict(
                    base,
                    estado="NO EXISTE",
                    registro="Crossref y DataCite",
                    detalle=f"ningún registro conoce el DOI {doi}",
                    DOI=doi,
                ))
            else:
                detalle = "; ".join(errores) or "respuesta incompleta de los registros"
                informe.append(dict(
                    base,
                    estado="ERROR",
                    registro="Crossref y DataCite",
                    detalle=f"no se pudo verificar el DOI {doi}: {detalle}",
                    DOI=doi,
                ))
            continue

        sim = parecido(e.get("title", ""), titulo_real or "")
        if sim < 0.60:
            informe.append(dict(
                base,
                estado="NO COINCIDE",
                registro=registro,
                detalle=(f"el DOI existe pero corresponde a "
                         f"«{(titulo_real or '')[:120]}»"),
                DOI=doi,
                titulo_registrado=titulo_real or "",
                similitud_titulo=round(sim, 4),
            ))
        else:
            informe.append(dict(
                base,
                estado="VERIFICADA",
                registro=registro,
                detalle=f"título registrado: {(titulo_real or '')[:120]}",
                DOI=doi,
                titulo_registrado=titulo_real or "",
                similitud_titulo=round(sim, 4),
                citable=True,
            ))
    return informe


def verificar(entradas: list[dict]) -> list[tuple[dict, str, str]]:
    """API histórica: devuelve ``(entrada, estado, detalle)`` por registro."""
    detallado = verificar_detallado(entradas)
    return [
        (entrada, "ok" if resultado["citable"] else resultado["estado"],
         resultado["detalle"])
        for entrada, resultado in zip(entradas, detallado, strict=True)
    ]


def construir_manifiesto(resultados: list[dict], fecha: str | None = None) -> dict:
    """Construye el contrato auditable que consumen los pasos posteriores."""
    bloqueantes = [r.get("id") or "<sin-id>" for r in resultados
                   if not r.get("citable")]
    citables = [r["id"] for r in resultados if r.get("citable") and r.get("id")]
    instante = fecha or (resultados[0]["fecha"] if resultados else fecha_utc())
    estado = "APROBADO" if not bloqueantes else "BLOQUEADO"
    return {
        "version": 1,
        "estado": estado,
        "registro": "Crossref, DataCite o confirmación manual explícita",
        "detalle": (f"{len(citables)} referencia(s) citable(s); "
                    f"{len(bloqueantes)} bloqueante(s)"),
        "fecha": instante,
        "archivo_confirmaciones": f"fuentes/{ARCHIVO_CONFIRMACIONES}",
        "citables": citables,
        "bloqueantes": bloqueantes,
        "referencias": resultados,
    }


def guardar_manifiesto(ruta: Path, resultados: list[dict]) -> dict:
    manifiesto = construir_manifiesto(resultados)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifiesto


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
    # citeproc conserva en ``bib.keys`` el orden exacto que aplica al ordenar
    # la bibliografía. Emparejar la salida con ``fuente`` (orden de entrada)
    # mezcla las claves cuando APA reordena por autor.
    bib.sort()
    referencias = [str(x) for x in bib.bibliography()]
    # el mapa clave -> entrada, para que quien produzca el documento no tenga
    # que adivinar qué entrada corresponde a qué cita
    por_clave = dict(zip(bib.keys, referencias, strict=True))
    # la cita en el texto tiene que salir del mismo motor que la referencia,
    # o el "et al." y el orden de autores se desincronizan
    en_texto = {k: str(bib.cite(c, lambda _: None)) for k, c in citas.items()}
    return referencias, en_texto, por_clave


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--carpeta", type=Path, required=True)
    p.add_argument("--verificar", action="store_true")
    p.add_argument("--locale", default="es-ES", help="es-ES | en-US")
    p.add_argument("--salida", default="salida/bibliografia.md")
    p.add_argument(
        "--confirmaciones",
        default=f"fuentes/{ARCHIVO_CONFIRMACIONES}",
        help="JSON explícito para confirmar obras legítimas sin DOI",
    )
    p.add_argument(
        "--manifiesto",
        default=f"fuentes/{ARCHIVO_MANIFIESTO}",
        help="rastro JSON de la verificación",
    )
    args = p.parse_args(argv)

    biblioteca = args.carpeta / "fuentes" / "biblioteca.json"
    if not biblioteca.exists():
        sys.exit(f"no hay {biblioteca} — usa buscar.py primero")
    try:
        entradas = json.loads(biblioteca.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"{biblioteca} no es JSON válido: {exc}", file=sys.stderr)
        return 2
    if not isinstance(entradas, list):
        print(f"{biblioteca} debe contener una lista de referencias", file=sys.stderr)
        return 2
    if not entradas:
        sys.exit("la biblioteca está vacía")

    usables = entradas
    bloqueantes: list[str] = []
    if args.verificar:
        print(f"verificando {len(entradas)} referencias contra Crossref y DataCite...\n")
        ruta_confirmaciones = args.carpeta / args.confirmaciones
        try:
            confirmaciones = cargar_confirmaciones(ruta_confirmaciones)
        except ValueError as exc:
            print(f"[CONFIGURACIÓN] {exc}", file=sys.stderr)
            return 2
        informe = verificar_detallado(entradas, confirmaciones)
        for resultado in informe:
            marca = "ok" if resultado["citable"] else resultado["estado"]
            manual = " · manual" if resultado.get("confirmada_manual") else ""
            print(f"[{marca:^13}] {resultado.get('id') or '?'}: "
                  f"{resultado['detalle']}{manual}")
        usables = [entrada for entrada, resultado in zip(entradas, informe, strict=True)
                   if resultado["citable"]]
        manifiesto_ruta = args.carpeta / args.manifiesto
        manifiesto = guardar_manifiesto(manifiesto_ruta, informe)
        bloqueantes = manifiesto["bloqueantes"]
        print(f"\n{len(usables)}/{len(informe)} referencias citables")
        print(f"{manifiesto_ruta.relative_to(args.carpeta)}: "
              f"estado {manifiesto['estado']}")
        if bloqueantes:
            print(f"{len(bloqueantes)} referencia(s) bloqueante(s); "
                  "no se ofrecen al generador")

    lineas, en_texto, por_clave = formatear(usables, args.locale)
    destino = args.carpeta / args.salida
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        "# Referencias\n\n" + "\n\n".join(lineas) + "\n",
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
    return 1 if bloqueantes else 0


if __name__ == "__main__":
    raise SystemExit(main())
