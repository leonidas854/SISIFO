"""El nombre de la carpeta es del usuario, no del programa.

Si pide `prueba_blockchain_problema_del_oraculo`, esa tiene que ser la carpeta:
convertir los guiones bajos en guiones le rompe rutas y referencias.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dockit" / "verificar"))

import pytest
from nuevo import slugificar


@pytest.mark.parametrize("entrada,esperado", [
    ("prueba_blockchain_problema_del_oraculo", "prueba_blockchain_problema_del_oraculo"),
    ("Mi Tesis 2026", "mi-tesis-2026"),
    ("tesis/../etc", "tesis-etc"),
    ("  espacios  ", "espacios"),
    ("acentós y ñ", "acentos-y-n"),
    ("TP-2 EQUIPO4", "tp-2-equipo4"),
])
def test_conserva_lo_valido_y_limpia_lo_peligroso(entrada, esperado):
    assert slugificar(entrada) == esperado


def test_nunca_produce_separadores_de_ruta():
    for malo in ("../fuera", "a/b", "a\\b", "/absoluto"):
        s = slugificar(malo)
        assert "/" not in s and "\\" not in s and ".." not in s
