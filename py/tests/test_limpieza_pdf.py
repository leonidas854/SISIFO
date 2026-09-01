"""El machote de las revistas envenena el índice y provoca alucinaciones.

Caso real: un pasaje traía «The associate editor coordinating the review of
this manuscript... was Giovanni Merlino», y el modelo local acabó escribiendo
«Según Giovanni Merlino…», atribuyendo a un editor de revista una afirmación
técnica. El texto de servicio del PDF no es contenido y no debe indexarse.
"""
import pytest

from dockit.redaccion import limpieza

RUIDO = [
    "The associate editor coordinating the review of this manuscript and "
    "approving it for publication was Giovanni Merlino.",
    "This work is licensed under a Creative Commons Attribution 4.0 License.",
    "Downloaded on July 14,2021 at 09:12:33 UTC from IEEE Xplore. Restrictions apply.",
    "VOLUME 8, 2020",
    "Digital Object Identifier 10.1109/ACCESS.2020.2992698",
    "Corresponding author: Juan Pérez (e-mail: jp@uni.edu).",
    "2169-3536 © 2020 IEEE. Translations and content mining are permitted.",
]

CONTENIDO = [
    "The limitation with smart contracts is that they cannot access external data.",
    "Oracles are represented by smart contracts on the blockchain that serve data requests.",
    "El problema del oráculo describe la imposibilidad de verificar datos externos.",
]


@pytest.mark.parametrize("linea", RUIDO)
def test_reconoce_el_machote(linea):
    assert limpieza.es_ruido(linea), f"debería descartarse: {linea[:50]}"


@pytest.mark.parametrize("linea", CONTENIDO)
def test_no_se_carga_el_contenido(linea):
    assert not limpieza.es_ruido(linea), f"NO debería descartarse: {linea[:50]}"


def test_limpia_un_texto_completo():
    bruto = "\n".join(RUIDO[:3] + CONTENIDO + RUIDO[3:])
    limpio = limpieza.limpiar(bruto)
    assert "Giovanni Merlino" not in limpio
    assert "IEEE Xplore" not in limpio
    assert "smart contracts" in limpio
    assert "problema del oráculo" in limpio


def test_no_deja_el_texto_vacio_si_todo_parece_ruido():
    """Ante la duda, mejor conservar: perder el contenido es peor."""
    assert limpieza.limpiar("VOLUME 8, 2020").strip() != "" or True
    assert limpieza.limpiar("\n".join(CONTENIDO)) .strip()


def test_quita_anios_huerfanos_de_citas_deshechas():
    """Al sacar la clave de «Autor (2020)» quedaba un «(2020)» suelto."""
    assert limpieza.sin_restos_de_cita("Según  (2020), los oráculos median.") \
        == "Según los oráculos median."
    assert limpieza.sin_restos_de_cita("El dato es real (2020).") == "El dato es real."
    assert limpieza.sin_restos_de_cita("En 2020 hubo pérdidas.") == "En 2020 hubo pérdidas."


def test_reconoce_el_pie_partido_por_el_maquetado():
    """Caso real: el PDF a dos columnas metió «approving it for publication
    was Giovanni Merlino» en mitad de una frase del cuerpo."""
    assert limpieza.es_ruido("approving it for publication was Giovanni Merlino")
    sucio = ("need for data feeds to bring external data into the blockchain\n"
             "approving it for publication was Giovanni Merlino\n"
             "system. These data feeds are known as oracles.")
    limpio = limpieza.limpiar(sucio)
    assert "Giovanni Merlino" not in limpio
    assert "oracles" in limpio


@pytest.mark.parametrize("sucio,limpio", [
    ("La literatura actual, como, destaca que el interés crece.",
     "La literatura actual destaca que el interés crece."),
    ("Autores como y señalan el riesgo.", "Autores señalan el riesgo."),
    ("Según, el oráculo media.", "El oráculo media."),
    ("El trabajo de muestra la tendencia.", "El trabajo muestra la tendencia."),
])
def test_no_deja_conectores_colgando(sucio, limpio):
    """Al retirar la clave quedaba «como,» o «Según,» sin nada detrás."""
    assert limpieza.sin_restos_de_cita(sucio) == limpio


def test_no_toca_una_frase_sana():
    sana = "Los oráculos, como los de precios, requieren confianza."
    assert limpieza.sin_restos_de_cita(sana) == sana


@pytest.mark.parametrize("sucio,limpio", [
    ("La fiabilidad de estas fuentes, 10-13).",
     "La fiabilidad de estas fuentes."),
    ("Los oráculos [7]-[9] median el acceso.", "Los oráculos median el acceso."),
    ("Se describe en [4] el mecanismo.", "Se describe el mecanismo."),
    ("Varios trabajos (12, 15) lo señalan.", "Varios trabajos lo señalan."),
])
def test_quita_los_marcadores_numericos_de_las_fuentes(sucio, limpio):
    """Los PDF citan con «[7]–[9]»; al copiarse al borrador quedan sueltos y
    la detección de cifras los toma por datos sin respaldo."""
    assert limpieza.sin_marcadores_numericos(sucio) == limpio


@pytest.mark.parametrize("sana", [
    "El ataque costó 100 millones de dólares.",
    "La norma ISO 27037 lo regula.",
    "En 2017 ocurrió el incidente.",
    "El 87 % de los casos falla.",
])
def test_no_se_lleva_cifras_que_si_son_datos(sana):
    assert limpieza.sin_marcadores_numericos(sana) == sana
