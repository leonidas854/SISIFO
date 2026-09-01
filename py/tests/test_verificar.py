"""Tests del verificador de entrega.

El regex de citas tenía un fallo silencioso: citeproc emite «et al.» con
espacio duro (U+00A0) y APA usa «&» para dos autores. El verificador contaba
cero citas en documentos que sí las tenían, y eso es peor que no comprobar:
da una señal falsa de que algo está mal cuando está bien.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dockit" / "verificar"))

import pytest
from verificar import RE_CITA, normalizar_espacios


@pytest.mark.parametrize("cita", [
    "(Nath et al., 2024)",
    "(Nath et al., 2024)",          # espacio duro, lo que produce citeproc
    "(Shah et al., 2017)",
    "(García, 2020)",
    "(Ćosić & Bača, 2010)",             # dos autores: APA usa &
    "(Ćosić & Bača, 2010)",
    "(Pérez-Gómez, 2019a)",             # sufijo de desambiguación
    "(Wenqi et al., 2020)",
])
def test_regex_reconoce_citas_apa_reales(cita):
    assert RE_CITA.search(normalizar_espacios(cita)), f"no reconoce {cita!r}"


@pytest.mark.parametrize("noes", [
    "(2024)",                  # solo un año no es una cita
    "(Im)proving chain",       # paréntesis dentro de un título
    "(ver capítulo 3)",
])
def test_regex_no_inventa_citas(noes):
    assert not RE_CITA.search(normalizar_espacios(noes)), f"no debería casar {noes!r}"


def test_cuenta_las_citas_de_un_texto_completo():
    texto = normalizar_espacios(
        "La cadena documenta cada traspaso (Nath et al., 2024). "
        "Otros lo discuten (Ćosić & Bača, 2010). "
        "El coste sube (Shah et al., 2017).")
    assert len(RE_CITA.findall(texto)) == 3
