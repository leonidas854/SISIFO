#!/usr/bin/env python3
"""Compone láminas fotográficas 16:9, siempre en dos filas.

Los rótulos se dibujan localmente sobre una banda blanca, fuera de la foto. De
este modo no se delega texto al modelo generativo y cada panel puede recortarse
o reutilizarse de manera independiente.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
FUENTE_PREDETERMINADA = ROOT.parent / "TEMAS_CON_IMAGENES" / "herramientas" / "fonts" / "Montserrat-Bold.ttf"
VERDE = "#0B4B2A"
BORDE = "#D7DDD9"


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("planes", type=Path, nargs="+")
    parser.add_argument("--imagenes", type=Path, required=True)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--fuente", type=Path, default=FUENTE_PREDETERMINADA)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--max-columnas", type=int, default=7)
    parser.add_argument("--permitir-faltantes", action="store_true")
    return parser.parse_args()


def localizar(raiz: Path, tema: int, panel_id: str) -> Path | None:
    base = raiz / f"tema{tema:02d}" / panel_id
    for extension in (".png", ".jpg", ".jpeg", ".webp"):
        candidato = base.with_suffix(extension)
        if candidato.exists():
            return candidato
    return None


def partir_por_diapositiva(paneles: list[dict], maximo: int) -> list[list[dict]]:
    """Balancea hojas y favorece cantidades pares para llenar las dos filas."""
    total = len(paneles)
    if not total:
        return []
    numero_hojas = math.ceil(total / maximo)
    objetivo = total / numero_hojas

    # DP sobre tamaños de hoja. Una hoja impar deja una celda blanca, por eso
    # recibe una pequeña penalización cuando existe una solución toda par.
    estado: dict[tuple[int, int], tuple[float, list[int]]] = {(0, 0): (0.0, [])}
    for hechas in range(numero_hojas):
        for (usados, h), (costo, tamanos) in list(estado.items()):
            if h != hechas:
                continue
            hojas_restantes = numero_hojas - hechas - 1
            for tamano in range(maximo, 0, -1):
                nuevo_usados = usados + tamano
                restante = total - nuevo_usados
                if restante < hojas_restantes or restante > hojas_restantes * maximo:
                    continue
                nuevo_costo = costo + (tamano - objetivo) ** 2 + (8.0 if tamano % 2 else 0.0)
                clave_estado = (nuevo_usados, hechas + 1)
                previo = estado.get(clave_estado)
                if previo is None or nuevo_costo < previo[0]:
                    estado[clave_estado] = (nuevo_costo, tamanos + [tamano])
    final = estado.get((total, numero_hojas))
    if final is None:
        raise RuntimeError("No se pudo dividir el inventario en hojas válidas")
    hojas = []
    inicio = 0
    for tamano in final[1]:
        hojas.append(paneles[inicio:inicio + tamano])
        inicio += tamano
    return hojas


def envolver(texto: str, fuente: ImageFont.FreeTypeFont, ancho: int, dibujo: ImageDraw.ImageDraw) -> list[str]:
    palabras = texto.upper().split()
    lineas: list[str] = []
    actual = ""
    for palabra in palabras:
        candidato = palabra if not actual else actual + " " + palabra
        if dibujo.textbbox((0, 0), candidato, font=fuente)[2] <= ancho:
            actual = candidato
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def ajustar_rotulo(texto: str, ruta_fuente: Path, ancho: int, alto: int, dibujo: ImageDraw.ImageDraw):
    for tamano in range(32, 15, -1):
        fuente = ImageFont.truetype(str(ruta_fuente), tamano)
        lineas = envolver(texto, fuente, ancho, dibujo)
        caja = dibujo.textbbox((0, 0), "Ag", font=fuente)
        paso = caja[3] - caja[1] + 4
        # `envolver` separa por palabras. Una palabra larga puede quedar sola
        # y superar el ancho aunque el número y alto de líneas sean válidos.
        # También comprobamos el ancho real para impedir que invada la celda
        # vecina (por ejemplo, "COMPLEMENTACIÓN").
        anchos = [dibujo.textbbox((0, 0), linea, font=fuente)[2] for linea in lineas]
        if len(lineas) <= 5 and len(lineas) * paso <= alto and all(valor <= ancho for valor in anchos):
            return fuente, lineas, paso
    fuente = ImageFont.truetype(str(ruta_fuente), 15)
    lineas = envolver(texto, fuente, ancho, dibujo)[:5]
    if len(envolver(texto, fuente, ancho, dibujo)) > 5 and lineas:
        lineas[-1] = lineas[-1].rstrip(" .") + "…"
    return fuente, lineas, 20


def componer_hoja(paneles: list[dict], tema: int, numero: int, args, manifiesto: list[dict]) -> Path:
    columnas = math.ceil(len(paneles) / 2)
    if columnas > args.max_columnas:
        raise ValueError(f"La hoja necesita {columnas} columnas, máximo {args.max_columnas}")
    lienzo = Image.new("RGB", (args.width, args.height), "white")
    dibujo = ImageDraw.Draw(lienzo)
    margen = 16
    separacion_x = 10
    separacion_y = 14
    ancho_celda = (args.width - 2 * margen - (columnas - 1) * separacion_x) // columnas
    alto_celda = (args.height - 2 * margen - separacion_y) // 2
    alto_rotulo = max(112, int(alto_celda * 0.23))
    destino = args.salida / f"tema{tema:02d}" / f"tema{tema:02d}_lamina_{numero:02d}.jpg"

    for indice, panel in enumerate(paneles):
        fila = indice // columnas
        columna = indice % columnas
        x = margen + columna * (ancho_celda + separacion_x)
        y = margen + fila * (alto_celda + separacion_y)
        dibujo.rectangle((x, y, x + ancho_celda, y + alto_celda), fill="white", outline=BORDE, width=2)
        fuente, lineas, paso = ajustar_rotulo(
            panel["rotulo"], args.fuente, ancho_celda - 18, alto_rotulo - 12, dibujo
        )
        alto_texto = len(lineas) * paso
        ty = y + max(6, (alto_rotulo - alto_texto) // 2)
        for linea in lineas:
            caja = dibujo.textbbox((0, 0), linea, font=fuente)
            tx = x + (ancho_celda - (caja[2] - caja[0])) // 2
            dibujo.text((tx, ty), linea, font=fuente, fill=VERDE)
            ty += paso

        ruta = localizar(args.imagenes, tema, panel["id"])
        foto_y = y + alto_rotulo
        foto_alto = alto_celda - alto_rotulo
        if ruta:
            with Image.open(ruta) as original:
                foto = ImageOps.fit(
                    original.convert("RGB"), (ancho_celda - 4, foto_alto - 4),
                    method=Image.Resampling.LANCZOS, centering=(0.5, 0.48),
                )
            lienzo.paste(foto, (x + 2, foto_y + 2))
        elif args.permitir_faltantes:
            dibujo.rectangle((x + 2, foto_y + 2, x + ancho_celda - 2, y + alto_celda - 2), fill="#F1F3F2")
            marca = "PENDIENTE"
            fuente_marca = ImageFont.truetype(str(args.fuente), 18)
            caja = dibujo.textbbox((0, 0), marca, font=fuente_marca)
            dibujo.text((x + (ancho_celda - caja[2]) // 2, foto_y + (foto_alto - caja[3]) // 2), marca,
                         font=fuente_marca, fill="#7A827D")
        else:
            raise FileNotFoundError(f"Falta la fotografía de {panel['id']}")

        manifiesto.append({
            "tema": tema, "lamina": numero, "fila": fila + 1, "columna": columna + 1,
            "id": panel["id"], "diapositiva": panel["diapositiva"],
            "orden_en_diapositiva": panel["orden_en_diapositiva"],
            "rotulo": panel["rotulo"], "imagen": str(ruta) if ruta else None,
            "archivo_lamina": str(destino),
        })

    destino.parent.mkdir(parents=True, exist_ok=True)
    lienzo.save(destino, "JPEG", quality=96, subsampling=0, optimize=True)
    return destino


def main() -> int:
    args = argumentos()
    if not args.fuente.exists():
        raise SystemExit(f"No existe la fuente: {args.fuente}")
    args.salida.mkdir(parents=True, exist_ok=True)
    manifiesto: list[dict] = []
    creadas = []
    maximo = args.max_columnas * 2
    for plan in args.planes:
        data = json.loads(plan.read_text(encoding="utf-8"))
        tema = int(data["tema"])
        paneles = data["paneles"]
        hojas = partir_por_diapositiva(paneles, maximo)
        for numero, hoja in enumerate(hojas, 1):
            creadas.append(str(componer_hoja(hoja, tema, numero, args, manifiesto)))
    (args.salida / "manifiesto_laminas.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    campos = [
        "tema", "diapositiva", "orden_en_diapositiva", "id", "rotulo",
        "lamina", "fila", "columna", "imagen", "archivo_lamina",
    ]
    with (args.salida / "indice_para_powerpoint.csv").open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows({campo: fila.get(campo) for campo in campos} for fila in manifiesto)
    print(json.dumps({"laminas": len(creadas), "paneles": len(manifiesto), "archivos": creadas},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
