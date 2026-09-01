#!/usr/bin/env python3
"""Extrae cada celda de las grillas imagegen como fotografía individual."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageFilter


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("trabajos", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--ancho-minimo", type=int, default=1024)
    parser.add_argument("--permitir-faltantes", action="store_true")
    return parser.parse_args()


def recortar_borde_blanco(celda: Image.Image) -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Elimina únicamente el fino separador blanco generado entre celdas."""
    gris = celda.convert("L")
    mascara = gris.point(lambda valor: 255 if valor < 246 else 0)
    caja = mascara.getbbox()
    if caja is None:
        return celda, (0, 0, celda.width, celda.height)
    # No permite que una zona de cielo claro recorte más del 4 % de la celda.
    max_x = max(2, round(celda.width * 0.04))
    max_y = max(2, round(celda.height * 0.04))
    izquierda = min(caja[0], max_x)
    arriba = min(caja[1], max_y)
    derecha = max(caja[2], celda.width - max_x)
    abajo = max(caja[3], celda.height - max_y)
    caja_segura = (izquierda, arriba, derecha, abajo)
    return celda.crop(caja_segura), caja_segura


def agrupar_consecutivos(valores: list[int]) -> list[tuple[int, int]]:
    if not valores:
        return []
    grupos = []
    inicio = anterior = valores[0]
    for valor in valores[1:]:
        if valor == anterior + 1:
            anterior = valor
            continue
        grupos.append((inicio, anterior + 1))
        inicio = anterior = valor
    grupos.append((inicio, anterior + 1))
    return grupos


def detectar_separadores(imagen: Image.Image, eje: str, esperados: int) -> list[tuple[int, int]]:
    """Detecta bandas blancas que cruzan la grilla de extremo a extremo."""
    if esperados <= 0:
        return []
    pixeles = imagen.load()
    ancho, alto = imagen.size
    perfil = []
    if eje == "x":
        muestras = range(0, alto, max(1, alto // 300))
        total = len(muestras)
        for x in range(ancho):
            blancos = sum(1 for y in muestras if min(pixeles[x, y]) >= 240)
            perfil.append(blancos / total)
        limite = ancho
    else:
        muestras = range(0, ancho, max(1, ancho // 400))
        total = len(muestras)
        for y in range(alto):
            blancos = sum(1 for x in muestras if min(pixeles[x, y]) >= 240)
            perfil.append(blancos / total)
        limite = alto

    partes = esperados + 1
    paso = limite / partes

    # Primera vía: localizar todas las bandas finas que son blancas a lo largo
    # de casi todo el eje. Imagegen no siempre reparte columnas iguales (en una
    # grilla real hubo saltos de hasta el 46 % respecto de la posición ideal),
    # de modo que buscar sólo alrededor de i * paso puede perder separadores
    # válidos. Elegimos por programación dinámica la secuencia ordenada que más
    # se aproxima a las posiciones ideales.
    posiciones_blancas = [i for i, valor in enumerate(perfil) if valor >= 0.72]
    bandas = agrupar_consecutivos(posiciones_blancas)
    ancho_maximo = max(12, round(paso * 0.08))
    margen_exterior = max(8, round(limite * 0.008))
    bandas = [
        (a, b) for a, b in bandas
        if a >= margen_exterior and b <= limite - margen_exterior and 1 <= b - a <= ancho_maximo
    ]
    if len(bandas) >= esperados:
        centros = [(a + b - 1) / 2 for a, b in bandas]
        infinito = float("inf")
        costos = [[infinito] * len(bandas) for _ in range(esperados)]
        previos = [[-1] * len(bandas) for _ in range(esperados)]
        for j, centro in enumerate(centros):
            costos[0][j] = (centro - paso) ** 2
        for k in range(1, esperados):
            ideal = (k + 1) * paso
            for j in range(k, len(bandas)):
                candidatos = [
                    (costos[k - 1][i] + (centros[j] - ideal) ** 2, i)
                    for i in range(k - 1, j) if costos[k - 1][i] < infinito
                ]
                if candidatos:
                    costos[k][j], previos[k][j] = min(candidatos)
        ultimo = min(range(esperados - 1, len(bandas)), key=lambda j: costos[-1][j])
        indices = [ultimo]
        for k in range(esperados - 1, 0, -1):
            ultimo = previos[k][ultimo]
            indices.append(ultimo)
        indices.reverse()
        elegidas = [bandas[i] for i in indices]
        bordes = [0.0] + [(a + b - 1) / 2 for a, b in elegidas] + [float(limite)]
        anchos = [b - a for a, b in zip(bordes, bordes[1:])]
        if all(0.38 * paso <= ancho <= 1.62 * paso for ancho in anchos):
            return elegidas

    # Segunda vía: búsqueda local alrededor de las posiciones teóricas. Sirve
    # para gutters algo grises que no alcanzan el 72 % de blanco puro.
    suavizado = []
    radio = 3
    for i in range(limite):
        a = max(0, i - radio)
        b = min(limite, i + radio + 1)
        suavizado.append(sum(perfil[a:b]) / (b - a))
    grupos = []
    for indice in range(1, partes):
        centro = indice * paso
        a = max(2, round(centro - paso * 0.43))
        b = min(limite - 2, round(centro + paso * 0.43))
        pico = max(range(a, b), key=lambda pos: suavizado[pos])
        # Los separadores de imagegen suelen medir apenas 2–3 px. Tras el
        # suavizado de siete muestras, una banda perfectamente blanca puede
        # alcanzar sólo 0.20–0.35 aunque su perfil central sea 1.0. El umbral
        # anterior (0.38) descartaba esas bandas reales y activaba el reparto
        # geométrico de respaldo, con riesgo de conservar una franja vecina.
        if suavizado[pico] < 0.18:
            return []
        vecinos = [
            pos for pos in range(max(2, pico - 9), min(limite - 2, pico + 10))
            if perfil[pos] >= max(0.38, suavizado[pico] * 0.43)
        ]
        if vecinos:
            grupos.append((min(vecinos), max(vecinos) + 1))
        else:
            grupos.append((max(2, pico - 1), min(limite - 2, pico + 2)))
    if any(a2 <= b1 for (_a1, b1), (a2, _b2) in zip(grupos, grupos[1:])):
        return []
    return grupos


def limites_desde_separadores(limite: int, separadores: list[tuple[int, int]], partes: int) -> list[tuple[int, int]]:
    if len(separadores) != partes - 1:
        return [(round(i * limite / partes), round((i + 1) * limite / partes)) for i in range(partes)]
    limites = []
    inicio = 0
    for a, b in separadores:
        limites.append((inicio, a))
        inicio = b
    limites.append((inicio, limite))
    return limites


def main() -> int:
    args = argumentos()
    data = json.loads(args.trabajos.read_text(encoding="utf-8"))
    manifiesto = []
    faltantes = []
    extraidos = 0
    for trabajo in data["trabajos"]:
        origen = Path(trabajo["destino"])
        if not origen.exists():
            faltantes.append(trabajo["id"])
            if args.permitir_faltantes:
                continue
            raise FileNotFoundError(origen)
        with Image.open(origen) as fuente:
            fuente = fuente.convert("RGB")
            ancho, alto = fuente.size
            columnas = int(trabajo["columnas"])
            filas = int(trabajo["filas"])
            separadores_y = detectar_separadores(fuente, "y", filas - 1)
            limites_y = limites_desde_separadores(alto, separadores_y, filas)
            limites_x_por_fila = []
            separadores_x_por_fila = []
            for y_inicio, y_fin in limites_y:
                fila_imagen = fuente.crop((0, y_inicio, ancho, y_fin))
                separadores_x = detectar_separadores(fila_imagen, "x", columnas - 1)
                separadores_x_por_fila.append(separadores_x)
                limites_x_por_fila.append(
                    limites_desde_separadores(ancho, separadores_x, columnas)
                )
            for indice, panel_id in enumerate(trabajo["paneles"]):
                fila = indice // columnas
                columna = indice % columnas
                x0, x1 = limites_x_por_fila[fila][columna]
                y0, y1 = limites_y[fila]
                celda = fuente.crop((x0, y0, x1, y1))
                celda, ajuste = recortar_borde_blanco(celda)
                if celda.width < args.ancho_minimo:
                    escala = args.ancho_minimo / celda.width
                    nuevo = (args.ancho_minimo, round(celda.height * escala))
                    celda = celda.resize(nuevo, Image.Resampling.LANCZOS)
                    celda = celda.filter(ImageFilter.UnsharpMask(radius=1.1, percent=45, threshold=3))
                destino = args.salida / f"tema{int(trabajo['tema']):02d}" / f"{panel_id}.jpg"
                destino.parent.mkdir(parents=True, exist_ok=True)
                celda.save(destino, "JPEG", quality=96, subsampling=0, optimize=True)
                extraidos += 1
                manifiesto.append({
                    "id": panel_id, "tema": int(trabajo["tema"]), "lamina": int(trabajo["lamina"]),
                    "fila": fila + 1, "columna": columna + 1, "origen": str(origen),
                    "caja_grilla": [x0, y0, x1, y1], "ajuste_borde": list(ajuste),
                    "separadores_detectados": bool(separadores_x_por_fila[fila]) and bool(separadores_y),
                    "destino": str(destino), "tamano": list(celda.size),
                })
    args.salida.mkdir(parents=True, exist_ok=True)
    (args.salida / "manifiesto_recortes.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"extraidos": extraidos, "grillas_faltantes": faltantes}, ensure_ascii=False, indent=2))
    return 0 if not faltantes else 1


if __name__ == "__main__":
    raise SystemExit(main())
