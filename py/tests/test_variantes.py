"""Producir no puede destruir lo que ya revisaste a mano.

El usuario abre el .pptx en OnlyOffice, lo retoca y lo usa. Si la siguiente
pasada lo pisa en silencio, pierde el trabajo. Además quiere varias versiones:
una por pasada, o una por tema que se vaya desarrollando.
"""
from pathlib import Path

import pytest

from dockit.generadores import destino_libre, generar_desde_guion

GUION = {"tipo": "docx", "titulo": "T", "bloques": [
    {"clase": "parrafo", "texto": "Algo."}]}


def test_no_pisa_un_archivo_existente(tmp_path):
    ya = tmp_path / "informe.docx"
    ya.write_text("lo que revisé a mano")
    nuevo = destino_libre(str(ya))
    assert nuevo != str(ya), "no puede devolver la misma ruta"
    assert ya.read_text() == "lo que revisé a mano", "el original sigue intacto"
    assert "v2" in nuevo


def test_va_numerando_las_pasadas(tmp_path):
    base = tmp_path / "informe.docx"
    creados = []
    for _ in range(3):
        d = destino_libre(str(base))
        Path(d).write_text("x")
        creados.append(d)
    assert len(set(creados)) == 3, "cada pasada necesita su propio archivo"
    assert any("v2" in c for c in creados) and any("v3" in c for c in creados)


def test_si_no_existe_usa_el_nombre_pedido(tmp_path):
    d = destino_libre(str(tmp_path / "informe.docx"))
    assert d.endswith("informe.docx")


def test_variante_con_nombre_para_cada_tema(tmp_path):
    """«diapos según los temas que se vayan desarrollando»."""
    d = destino_libre(str(tmp_path / "diapos.pptx"), variante="tema3")
    assert d.endswith("diapos-tema3.pptx")


def test_sobrescribir_explicito_si_lo_pides(tmp_path):
    ya = tmp_path / "informe.docx"
    ya.write_text("viejo")
    assert destino_libre(str(ya), sobrescribir=True) == str(ya)


def test_generar_respeta_el_archivo_previo(tmp_path):
    destino = tmp_path / "x.docx"
    r1 = generar_desde_guion(GUION, str(destino))
    r2 = generar_desde_guion(GUION, str(destino))
    assert r1["ruta"] != r2["ruta"], "la segunda pasada no puede pisar la primera"
