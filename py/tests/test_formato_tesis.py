"""El formato de tesis del BRIEF tiene que llegar al documento.

Si el BRIEF pide interlineado doble y márgenes de 2,54 cm —lo que exige APA 7—
y el generador los ignora, el trabajo se rechaza por formato aunque el
contenido sea impecable.
"""
from docx import Document
from docx.shared import Cm

from dockit.generadores import docx as gd

GUION = {"tipo": "docx", "titulo": "T", "bloques": [
    {"clase": "titulo", "nivel": 1, "texto": "Introducción"},
    {"clase": "parrafo", "texto": "Un párrafo de prueba con suficiente texto."}]}

FORMATO = {"tipografia": "Times New Roman", "tamano_pt": 12,
           "margenes_cm": 2.54, "interlineado": 2.0}


def generar(tmp_path, formato=FORMATO):
    d = tmp_path / "t.docx"
    gd.generar(GUION, str(d), {}, {}, formato)
    return Document(str(d))


def test_margenes_de_una_pulgada(tmp_path):
    sec = generar(tmp_path).sections[0]
    for lado, valor in (("superior", sec.top_margin), ("inferior", sec.bottom_margin),
                        ("izquierdo", sec.left_margin), ("derecho", sec.right_margin)):
        assert abs(valor.cm - 2.54) < 0.02, f"margen {lado}: {valor.cm:.2f} cm"


def test_interlineado_doble(tmp_path):
    d = generar(tmp_path)
    assert abs(d.styles["Normal"].paragraph_format.line_spacing - 2.0) < 0.01, \
        "APA 7 pide interlineado doble y el BRIEF lo declara"


def test_tipografia_y_cuerpo_del_brief(tmp_path):
    normal = generar(tmp_path).styles["Normal"]
    assert normal.font.name == "Times New Roman"
    assert normal.font.size.pt == 12


def test_sin_ajustes_usa_valores_razonables(tmp_path):
    d = generar(tmp_path, formato={})
    assert d.styles["Normal"].font.size.pt >= 10
    assert d.sections[0].top_margin.cm > 1
