"""Vuelca las tablas del guion a una hoja de cálculo.

Sirve para revisar los datos aparte del documento y para que OnlyOffice o
Excel puedan graficarlos sin volver a teclearlos.
"""
from __future__ import annotations

import re
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from . import guion as G

CABECERA = PatternFill("solid", fgColor="E8ECEF")
ANCHO_MAX = 60


def _nombre_hoja(leyenda: str, n: int, usados: set[str]) -> str:
    """Excel no admite más de 31 caracteres ni ciertos signos en el nombre."""
    base = re.split(r"[.:]", leyenda or "")[0].strip() or f"Tabla {n}"
    base = re.sub(r"[\[\]\*/\\?:]", " ", base).strip()[:31] or f"Tabla {n}"
    nombre, i = base, 1
    while nombre in usados:
        i += 1
        sufijo = f" ({i})"
        nombre = base[:31 - len(sufijo)] + sufijo
    usados.add(nombre)
    return nombre


def _ajustar(hoja) -> None:
    for col in hoja.columns:
        ancho = max((len(str(c.value)) for c in col if c.value is not None),
                    default=8)
        hoja.column_dimensions[get_column_letter(col[0].column)].width = \
            min(ancho + 3, ANCHO_MAX)


def generar(guion: dict, destino: str, bibliografia: dict[str, str],
            en_texto: dict[str, str], formato: dict | None = None) -> dict:
    G.validar(guion, set(bibliografia) if bibliografia else None)

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    usados: set[str] = set()
    n = 0

    for b in guion["bloques"]:
        if b["clase"] != "tabla":
            continue
        n += 1
        hoja = wb.create_sheet(_nombre_hoja(b.get("leyenda", ""), n, usados))
        fila = 1
        if b.get("cabecera"):
            for j, texto in enumerate(b["cabecera"], 1):
                c = hoja.cell(fila, j, texto)
                c.font = Font(bold=True)
                c.fill = CABECERA
                c.alignment = Alignment(vertical="center", wrap_text=True)
            hoja.freeze_panes = "A2"
            fila += 1
        for f in b["filas"]:
            for j, valor in enumerate(f, 1):
                hoja.cell(fila, j, _numero_si_puede(valor))
            fila += 1
        if b.get("fuente"):
            hoja.cell(fila + 1, 1, f"Fuente: {b['fuente']}").font = \
                Font(italic=True, size=9)
        _ajustar(hoja)

    if bibliografia:
        hoja = wb.create_sheet(_nombre_hoja("Referencias", n + 1, usados))
        hoja.cell(1, 1, "Clave").font = Font(bold=True)
        hoja.cell(1, 2, "Referencia (APA 7)").font = Font(bold=True)
        for i, (clave, entrada) in enumerate(sorted(bibliografia.items()), 2):
            hoja.cell(i, 1, clave)
            hoja.cell(i, 2, entrada).alignment = Alignment(wrap_text=True)
        hoja.column_dimensions["B"].width = ANCHO_MAX

    if not wb.sheetnames:
        wb.create_sheet("Sin datos")

    Path(destino).parent.mkdir(parents=True, exist_ok=True)
    wb.save(destino)
    return {"ruta": destino, "unidades": len(wb.sheetnames)}


def _numero_si_puede(v):
    """Un número guardado como texto no se puede graficar ni sumar."""
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip().replace(",", ".")
    try:
        return int(s) if s.isdigit() or (s.startswith("-") and s[1:].isdigit()) \
            else float(s)
    except ValueError:
        return v
