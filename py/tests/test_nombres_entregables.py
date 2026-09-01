"""Producir tiene que escribir los archivos que el BRIEF declara.

Si el BRIEF pide `salida/informe.docx` y producir escribe
`salida/mi_carpeta.docx`, el verificador dirá que falta el entregable aunque
esté hecho. El nombre no es cosmético: es el contrato entre las dos órdenes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dockit"))

import pytest
from producir import destino_declarado

BRIEF = {"entregables": [
    {"archivo": "salida/informe.docx", "tipo": "docx"},
    {"archivo": "salida/diapositivas.pptx", "tipo": "pptx"},
]}


def test_usa_el_nombre_que_declara_el_brief():
    assert destino_declarado(BRIEF, "docx", "carpeta") == "salida/informe.docx"
    assert destino_declarado(BRIEF, "pptx", "carpeta") == "salida/diapositivas.pptx"


def test_si_el_brief_no_lo_declara_cae_al_nombre_de_la_carpeta():
    assert destino_declarado(BRIEF, "xlsx", "mi-trabajo") == "salida/mi-trabajo.xlsx"


def test_sin_entregables_no_revienta():
    assert destino_declarado({}, "docx", "x") == "salida/x.docx"
    assert destino_declarado({"entregables": None}, "docx", "x") == "salida/x.docx"


def test_deduce_el_tipo_por_la_extension_si_falta():
    brief = {"entregables": [{"archivo": "salida/tesis.docx"}]}
    assert destino_declarado(brief, "docx", "x") == "salida/tesis.docx"
