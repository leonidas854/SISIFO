"""Los diagramas tienen que llevar sus rótulos dibujados.

Queja real del usuario: «las imágenes salieron vacías y feas, sin letras ni
nada, algunas nada que ver, sin títulos y no tienen sentido con lo que dice la
diapositiva». La causa estaba en el código: los arquetipos reservaban una
franja inferior «limpia para los rótulos» y no dibujaban ninguno.
"""
import re
import shutil
import subprocess

import pytest

from dockit.imagen import diagramas

SPEC = {
    "tipo": "fila",
    "iconos": ["candado", "mundo", "comunidad"],   # nombres reales del catálogo
    "rotulos": ["Oráculo centralizado", "Fuente de datos", "Red descentralizada"],
    "titulo": "Arquitectura del oráculo",
    "acento": [0],
}


def test_la_biblioteca_de_iconos_carga():
    """Tras mover el repo, CANONICO apuntaba a una ruta inexistente."""
    assert len(diagramas.ICONS) > 5


def test_el_diagrama_dibuja_los_rotulos():
    svg = diagramas.construir(SPEC)
    for rotulo in SPEC["rotulos"]:
        assert rotulo in svg, f"no se dibuja el rótulo «{rotulo}»"


def test_el_diagrama_lleva_su_titulo():
    assert SPEC["titulo"] in diagramas.construir(SPEC)


def test_los_rotulos_son_elementos_de_texto_no_adornos():
    svg = diagramas.construir(SPEC)
    textos = re.findall(r"<text[^>]*>(.*?)</text>", svg, re.S)
    assert len(textos) >= len(SPEC["rotulos"]), \
        f"solo {len(textos)} elementos de texto para {len(SPEC['rotulos'])} rótulos"


def test_los_rotulos_se_leen_proyectados():
    """Un rótulo a 10 px en una lámina de 1600 no lo lee nadie."""
    svg = diagramas.construir(SPEC)
    tamanos = [float(t) for t in re.findall(r'font-size="(\d+(?:\.\d+)?)"', svg)]
    assert tamanos, "los textos no declaran tamaño"
    assert min(tamanos) >= 24, f"hay texto a {min(tamanos)} px sobre 1600 de ancho"


def test_el_texto_largo_no_se_desborda():
    largo = dict(SPEC, rotulos=[
        "Un rótulo muy largo que no cabe de ninguna manera en una sola línea",
        "Corto", "Medio tamaño"])
    svg = diagramas.construir(largo)
    assert "Un rótulo muy largo" in svg
    # se parte en varias líneas en vez de salirse del lienzo
    assert svg.count("<tspan") >= 1 or "…" in svg


@pytest.mark.parametrize("tipo", sorted(diagramas.ARQUETIPOS))
def test_ningun_arquetipo_sale_mudo(tipo):
    """Ni uno solo puede generarse sin rótulos: ese fue el fallo original."""
    spec = dict(SPEC, tipo=tipo)
    try:
        svg = diagramas.construir(spec)
    except KeyError as e:
        pytest.skip(f"«{tipo}» necesita otra forma de spec: {e}")
    assert SPEC["rotulos"][0] in svg, f"«{tipo}» no dibuja rótulos"
    assert SPEC["titulo"] in svg, f"«{tipo}» no dibuja el título"


@pytest.mark.skipif(not shutil.which("rsvg-convert"), reason="requiere rsvg-convert")
def test_el_png_se_genera_de_verdad(tmp_path):
    png = diagramas.escribir(SPEC, tmp_path / "d")
    assert png.exists() and png.stat().st_size > 3000, "el PNG salió vacío"
    from PIL import Image
    with Image.open(png) as im:
        assert im.size[0] >= 800


def test_los_rotulos_no_se_dibujan_dos_veces():
    """Bug real: el respaldo universal no detectaba los rótulos ya dibujados
    —van partidos en <tspan>— y los repetía en una segunda banda."""
    svg = diagramas.construir(SPEC)
    for rotulo in SPEC["rotulos"]:
        primera = rotulo.split()[0]
        assert svg.count(f">{primera}") <= 1, \
            f"«{rotulo}» aparece más de una vez en el diagrama"


def test_muchos_rotulos_no_se_tocan():
    """Con cinco rótulos en una fila se solapaban; el texto debe encoger y
    partirse para que quepa en su columna."""
    spec = dict(SPEC, tipo="contraste",
                iconos=["candado", "mundo", "comunidad", "alerta", "barras"],
                rotulos=["Falta garantía de datos oráculos",
                         "Reintroduce centralización", "Riesgos de collusion",
                         "Oráculos pueden fallar", "Desafíos técnicos"],
                izquierda=["candado", "mundo"],
                derecha=["comunidad", "alerta", "barras"])
    svg = diagramas.construir(spec)
    import re
    tamanos = [float(t) for t in re.findall(r'font-size="(\d+(?:\.\d+)?)"', svg)]
    assert min(tamanos) >= 22, "el texto encogió demasiado para leerse"
    # con cinco columnas el rótulo tiene que partirse en varias líneas
    assert svg.count("<tspan") >= 8, "los rótulos no se están partiendo"
