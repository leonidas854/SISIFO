#!/usr/bin/env python3
"""Valida cobertura, archivos y duplicación de los paneles fotográficos."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("planes", type=Path, nargs="+")
    parser.add_argument("--imagenes", type=Path, required=True)
    parser.add_argument("--laminas", type=Path)
    parser.add_argument("--informe", type=Path)
    parser.add_argument("--umbral-dhash", type=int, default=3)
    return parser.parse_args()


def localizar(raiz: Path, tema: int, panel_id: str) -> Path | None:
    base = raiz / f"tema{tema:02d}" / panel_id
    for extension in (".png", ".jpg", ".jpeg", ".webp"):
        ruta = base.with_suffix(extension)
        if ruta.exists():
            return ruta
    return None


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def dhash(imagen: Image.Image, tamano: int = 12) -> int:
    gris = imagen.convert("L").resize((tamano + 1, tamano), Image.Resampling.LANCZOS)
    pixeles = list(gris.getdata())
    valor = 0
    for y in range(tamano):
        for x in range(tamano):
            valor = (valor << 1) | (pixeles[y * (tamano + 1) + x] > pixeles[y * (tamano + 1) + x + 1])
    return valor


def main() -> int:
    args = argumentos()
    paneles: list[dict] = []
    for plan in args.planes:
        data = json.loads(plan.read_text(encoding="utf-8"))
        for panel in data.get("paneles", []):
            copia = dict(panel)
            copia.setdefault("tema", data["tema"])
            copia["plan"] = str(plan)
            paneles.append(copia)

    ids = [p.get("id") for p in paneles]
    errores = []
    duplicados_id = [k for k, n in Counter(ids).items() if n > 1]
    if duplicados_id:
        errores.append({"ids_duplicados": duplicados_id})

    faltantes = []
    dimensiones_invalidas = []
    hashes: dict[str, list[str]] = defaultdict(list)
    perceptuales: list[tuple[str, int]] = []
    archivos = []
    for panel in paneles:
        tema = int(panel["tema"])
        ruta = localizar(args.imagenes, tema, panel["id"])
        if ruta is None:
            faltantes.append(panel["id"])
            continue
        archivos.append(str(ruta))
        try:
            with Image.open(ruta) as im:
                im.verify()
            with Image.open(ruta) as im:
                ancho, alto = im.size
                if ancho < 512 or alto < 512:
                    dimensiones_invalidas.append({"id": panel["id"], "tamano": [ancho, alto]})
                perceptuales.append((panel["id"], dhash(im)))
        except Exception as exc:
            errores.append({"archivo_invalido": str(ruta), "error": repr(exc)})
            continue
        hashes[sha256(ruta)].append(panel["id"])

    exactos = [grupo for grupo in hashes.values() if len(grupo) > 1]
    cercanos = []
    for i, (id_a, hash_a) in enumerate(perceptuales):
        for id_b, hash_b in perceptuales[i + 1:]:
            distancia = (hash_a ^ hash_b).bit_count()
            if distancia <= args.umbral_dhash:
                cercanos.append({"a": id_a, "b": id_b, "distancia": distancia})

    laminas_invalidas = []
    total_laminas = 0
    if args.laminas and args.laminas.exists():
        for ruta in sorted(args.laminas.glob("tema*/tema*_lamina_*.jpg")):
            total_laminas += 1
            with Image.open(ruta) as im:
                if im.size != (1920, 1080):
                    laminas_invalidas.append({"archivo": str(ruta), "tamano": list(im.size)})

    informe = {
        "paneles_planificados": len(paneles),
        "paneles_encontrados": len(archivos),
        "faltantes": faltantes,
        "dimensiones_invalidas": dimensiones_invalidas,
        "duplicados_exactos": exactos,
        "posibles_duplicados_perceptuales": cercanos,
        "laminas_encontradas": total_laminas,
        "laminas_invalidas": laminas_invalidas,
        "errores": errores,
        "estado": "OK" if not (faltantes or dimensiones_invalidas or exactos or laminas_invalidas or errores) else "REVISAR",
    }
    if args.informe:
        args.informe.parent.mkdir(parents=True, exist_ok=True)
        args.informe.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(informe, ensure_ascii=False, indent=2))
    return 0 if informe["estado"] == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
