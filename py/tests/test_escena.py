"""Imágenes realistas para las diapositivas, generadas en local con SDXL.

Los diagramas de iconos son demasiado abstractos: el usuario pide imágenes que
muestren de qué va la lámina. SDXL no sabe escribir texto, así que la regla es
la contraria a la del diagrama: la escena ilustra, y los rótulos los pone la
diapositiva.
"""
import pytest

from dockit.imagen import escena

PALETA = {"primary": "0B6B61", "accent": "F3B33D", "ink": "182126"}


def test_el_prompt_va_en_ingles_y_pide_realismo():
    p = escena.prompt_base("Riesgos del oráculo",
                           ["Manipulación de precios", "Centralización"], PALETA)
    bajo = p.lower()
    assert "photo" in bajo or "photograph" in bajo or "realistic" in bajo
    assert "text" not in bajo.split("negative")[0] or "no text" in bajo


def test_el_negativo_prohibe_texto_y_marcas():
    n = escena.PROMPT_NEGATIVO.lower()
    for prohibido in ("text", "watermark", "logo", "letters"):
        assert prohibido in n, f"el negativo debería excluir «{prohibido}»"


def test_la_paleta_entra_en_el_prompt():
    p = escena.prompt_base("T", ["Uno"], PALETA)
    assert "teal" in p.lower() or "0B6B61" in p or "green" in p.lower(), \
        "el color dominante de la lámina debería guiar la imagen"


def test_el_prompt_recoge_el_tema_de_la_lamina():
    p = escena.prompt_base("Infraestructura de datos",
                           ["Servidores y redes", "Flujo de información"], PALETA)
    bajo = p.lower()
    assert "server" in bajo or "data" in bajo or "network" in bajo, \
        "el prompt no menciona nada del contenido de la lámina"


def test_sin_vinetas_no_hay_escena():
    assert escena.prompt_base("Solo título", [], PALETA) is None


def test_detecta_si_puede_generar():
    assert isinstance(escena.disponible(), bool)


@pytest.mark.skipif(not escena.disponible(), reason="requiere SDXL en local")
def test_genera_una_imagen_de_verdad(tmp_path):
    ruta = escena.generar("Redes de datos", ["Servidores distribuidos"],
                          tmp_path, "e1", PALETA)
    assert ruta and ruta.exists() and ruta.stat().st_size > 20000
    from PIL import Image
    with Image.open(ruta) as im:
        assert im.size[0] >= 512


# ── el texto y la imagen se pelean por la misma GPU ─────────────────────

def test_sabe_qué_modelos_hay_que_descargar():
    """qwen2.5:7b ocupa 4,6 GB de los 7,6 de la 3070: SDXL no cabe al lado.
    Para cuando toca generar imágenes el texto ya está escrito, así que el
    modelo de lenguaje puede descargarse."""
    assert hasattr(escena, "liberar_gpu")


def test_liberar_gpu_no_revienta_sin_ollama(monkeypatch):
    monkeypatch.setattr(escena.shutil, "which", lambda _: None)
    escena.liberar_gpu(["qwen2.5:7b"])       # no debe lanzar


def test_liberar_gpu_pide_parar_los_modelos(monkeypatch):
    llamadas = []
    monkeypatch.setattr(escena.shutil, "which", lambda _: "/usr/bin/ollama")
    monkeypatch.setattr(escena.subprocess, "run",
                        lambda cmd, **k: llamadas.append(cmd))
    escena.liberar_gpu(["qwen2.5:7b", "bge-m3"])
    parados = [c[-1] for c in llamadas if "stop" in c]
    assert "qwen2.5:7b" in parados and "bge-m3" in parados


# ── variedad: dos láminas no pueden salir con la misma imagen ───────────

def test_no_repite_la_escena_base_en_la_misma_presentacion():
    """Bug real: «Planteamiento del problema» y «Riesgos» cayeron los dos en
    la escena de red y salió la misma imagen dos veces."""
    usadas: set[str] = set()
    a = escena.prompt_base("Planteamiento del problema",
                           ["Vulnerabilidad de la red", "Centralización"],
                           PALETA, usadas=usadas)
    b = escena.prompt_base("Riesgos y casos documentados",
                           ["Dependencia de la red", "Centralización"],
                           PALETA, usadas=usadas)
    assert a != b, "dos láminas recibieron exactamente el mismo prompt"


def test_cada_lamina_lleva_su_semilla():
    """Aunque el prompt coincida, la semilla distinta cambia la imagen."""
    t1 = escena.tarea("A", ["Uno"], PALETA, "/tmp/a.png", indice=1)
    t2 = escena.tarea("B", ["Dos"], PALETA, "/tmp/b.png", indice=2)
    assert t1["semilla"] != t2["semilla"]


def test_la_semilla_es_estable_para_la_misma_lamina():
    a = escena.tarea("A", ["Uno"], PALETA, "/tmp/a.png", indice=1)
    b = escena.tarea("A", ["Uno"], PALETA, "/tmp/a.png", indice=1)
    assert a["semilla"] == b["semilla"], "regenerar debe dar lo mismo"
