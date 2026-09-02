"""Los diagramas tienen que usar los colores de la diapositiva.

Las láminas van en verde azulado (#0B6B61) y los diagramas salían en oliva
(#455119), la paleta del proyecto policial. El resultado parecía pegado de
otra presentación.
"""
import re

import pytest

from dockit.imagen import diagramas, ilustrar

SPEC = {"tipo": "fila", "iconos": ["candado", "mundo"],
        "rotulos": ["Uno", "Dos"], "acento": [0]}

PALETA_LAMINA = {"primary": "0B6B61", "accent": "F3B33D",
                 "ink": "182126", "soft": "DCEDE9", "paper": "FFFFFF"}


def colores_de(svg: str) -> set[str]:
    return {c.upper() for c in re.findall(r"#([0-9A-Fa-f]{6})", svg)}


def test_el_diagrama_acepta_la_paleta_de_la_lamina():
    svg = diagramas.construir(dict(SPEC, paleta=PALETA_LAMINA))
    usados = colores_de(svg)
    assert "0B6B61" in usados, "no usa el color principal de la diapositiva"
    assert "455119" not in usados, "sigue usando el oliva del proyecto policial"


def test_sin_paleta_mantiene_la_de_siempre():
    usados = colores_de(diagramas.construir(SPEC))
    assert "455119" in usados, "sin paleta explícita no debe cambiar nada"


def test_el_fondo_del_diagrama_no_choca_con_el_de_la_lamina():
    svg = diagramas.construir(dict(SPEC, paleta=PALETA_LAMINA))
    fondo = re.search(r'<rect width="\d+" height="\d+" fill="#([0-9A-Fa-f]{6})"', svg)
    assert fondo, "el diagrama no declara fondo"
    assert fondo.group(1).upper() in ("FFFFFF", "F5F8F8", "DCEDE9"), \
        f"fondo {fondo.group(1)} sobre lámina blanca canta"


def test_ilustrar_pasa_la_paleta():
    spec = ilustrar.spec_para("T", ["Uno", "Dos"], paleta=PALETA_LAMINA)
    assert spec["paleta"]["primary"] == "0B6B61"
