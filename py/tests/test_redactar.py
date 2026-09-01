"""Redacción con modelo local, anclada a las fuentes.

El modelo local escribe, pero no puede inventar: solo se le entregan pasajes
recuperados del índice y solo puede citar claves ya verificadas. Lo que afirme
con una cifra tiene que quedar anclado a una cita literal de esos pasajes.
"""
import pytest

from dockit.redaccion import anclaje, plan


PASAJES = [
    {"fuente": "caldarelli2020understanding", "texto":
     "The oracle problem refers to the inability of blockchains to access "
     "external data without a trusted intermediary."},
    {"fuente": "sheldon2020auditing", "texto":
     "Price feed manipulation caused losses exceeding 100 million dollars in 2020."},
]
VERIFICADAS = {"caldarelli2020understanding", "sheldon2020auditing"}


def test_el_esquema_sale_del_indice_no_de_la_nada():
    secciones = plan.esquema_por_defecto("El problema del oráculo")
    assert len(secciones) >= 6, "una tesis necesita más de cinco secciones"
    titulos = [s["titulo"] for s in secciones]
    assert any("ntroducc" in t for t in titulos)
    assert any("onclusi" in t for t in titulos)


def test_solo_se_permiten_claves_verificadas():
    texto = "El oráculo es central (caldarelli2020understanding) y falla (inventada2020)."
    limpio, descartadas = anclaje.filtrar_citas(texto, VERIFICADAS)
    assert "inventada2020" not in limpio
    assert "caldarelli2020understanding" in limpio
    assert "inventada2020" in descartadas


def test_una_cifra_sin_pasaje_que_la_respalde_se_marca():
    afirmaciones = anclaje.extraer_afirmaciones(
        "Las pérdidas superaron los 100 millones de dólares en 2020.",
        PASAJES, VERIFICADAS)
    assert afirmaciones, "una cifra tiene que producir una afirmación que verificar"
    a = afirmaciones[0]
    assert a["fuente"] == "sheldon2020auditing"
    assert "100 million" in a["cita"] or "Price feed" in a["cita"]


def test_una_cifra_sin_ningun_pasaje_no_inventa_fuente():
    afirmaciones = anclaje.extraer_afirmaciones(
        "El 99,7 % de los oráculos falla los martes.", PASAJES, VERIFICADAS)
    assert afirmaciones
    assert not afirmaciones[0]["fuente"], \
        "si ningún pasaje lo respalda, no se le puede asignar una fuente"


def test_la_prosa_sin_datos_no_genera_afirmaciones():
    assert anclaje.extraer_afirmaciones(
        "El problema es conceptualmente relevante.", PASAJES, VERIFICADAS) == []


def test_el_prompt_prohibe_salirse_de_los_pasajes():
    p = plan.prompt_seccion("Introducción", "de qué va", PASAJES, "es")
    bajo = p.lower()
    assert "solo" in bajo or "únicamente" in bajo
    assert "no inventes" in bajo or "no añadas" in bajo
    assert PASAJES[0]["texto"][:40].lower() in bajo, "los pasajes deben ir en el prompt"


# ── bugs hallados redactando el trabajo del oráculo ─────────────────────

def test_la_clave_de_cita_no_cuenta_como_dato():
    """Bug real: `breiki2020trustworthy` lleva «2020» dentro, así que la
    detección de cifras la tomaba por un dato y exigía fuente para nada."""
    afirmaciones = anclaje.extraer_afirmaciones(
        "Según breiki2020trustworthy, los oráculos median el acceso externo.",
        PASAJES, VERIFICADAS)
    assert afirmaciones == [], \
        "una frase cuyo único número está dentro de la clave no es un dato"


def test_se_normalizan_las_citas_en_prosa():
    """El modelo escribe «Según clave2020, ...» en vez de «(clave2020)».
    Hay que reconocerlo igual, o la cita se pierde."""
    texto = "Según caldarelli2020understanding, el oráculo es un intermediario."
    limpio, claves = anclaje.normalizar_citas(texto, VERIFICADAS)
    assert "caldarelli2020understanding" not in limpio
    assert "caldarelli2020understanding" in claves
    assert "Según" in limpio and "intermediario" in limpio


def test_normalizar_citas_detecta_las_dos_formas():
    texto = ("El oráculo media (caldarelli2020understanding). "
             "Las pérdidas fueron altas según sheldon2020auditing.")
    limpio, claves = anclaje.normalizar_citas(texto, VERIFICADAS)
    assert set(claves) == VERIFICADAS
    assert "(" not in limpio or "understanding" not in limpio


def test_normalizar_no_toca_claves_no_verificadas():
    limpio, claves = anclaje.normalizar_citas(
        "Algo dice inventada2020fake y otra cosa.", VERIFICADAS)
    assert "inventada2020fake" not in claves


def test_el_prompt_prohibe_el_metatexto():
    """Bug real: llama3.2 escribía «La sección de Introducción presentará…»
    en vez de escribir la introducción."""
    p = plan.prompt_seccion("Introducción", "presentar el problema", PASAJES, "es")
    bajo = p.lower()
    assert "esta sección presenta" in bajo, "hay que darle el ejemplo de lo prohibido"
    assert "no describas" in bajo or "prohibido" in bajo
    assert "cita siempre" in bajo, "sin exigir cita, salen párrafos sin respaldo"


# ── guion de diapositivas: lo fundamental, no todo ───────────────────────

def test_las_vinetas_se_limpian_y_se_acotan():
    bruto = """- La primera idea importante del tema
2. Segunda idea, también relevante
* Tercera idea que merece la pena

Cuarta idea
Quinta idea
Sexta idea
Séptima idea que ya sobra"""
    v = plan.vinetas_desde(bruto, maximo=5)
    assert len(v) == 5, "una lámina con más de cinco viñetas es un muro"
    assert not any(x.startswith(("-", "*", "1", "2", "•")) for x in v), \
        "los guiones y números de la lista los pone el diseño, no el texto"
    assert all(x for x in v), "no puede colarse una viñeta vacía"


@pytest.mark.parametrize("preludio", [
    "Aquí tienes las viñetas:",
    "Aquí te presento las viñetas para la diapositiva:",
    "Aquí te dejo las viñetas para la diapositiva",
    "Claro, estas son las ideas principales:",
    "Viñetas:",
    "A continuación, las ideas clave de la sección:",
])
def test_las_vinetas_descartan_el_relleno_del_modelo(preludio):
    """El modelo local antepone una frase de cortesía que acababa impresa
    como primera viñeta de la diapositiva."""
    v = plan.vinetas_desde(f"{preludio}\nIdea uno\nIdea dos", maximo=5)
    assert v == ["Idea uno", "Idea dos"], f"se coló el preludio: {v}"


def test_no_confunde_una_vineta_legitima_con_relleno():
    v = plan.vinetas_desde("Las viñetas de datos externos son el problema\nOtra idea", 5)
    assert len(v) == 2, "una viñeta que habla de datos no es un preludio"


def test_guion_de_diapositivas_sigue_el_indice():
    secciones = [
        {"titulo": "Introducción", "vinetas": ["Idea A", "Idea B"]},
        {"titulo": "Conclusiones", "vinetas": ["Cierre"]},
    ]
    g = plan.guion_diapositivas("Mi trabajo", secciones)
    assert g["tipo"] == "pptx"
    titulos = [b["texto"] for b in g["bloques"] if b["clase"] == "titulo"]
    assert titulos == ["Introducción", "Conclusiones"], \
        "las láminas siguen el índice del informe, en su orden"
    listas = [b for b in g["bloques"] if b["clase"] == "lista"]
    assert len(listas) == 2 and listas[0]["items"] == ["Idea A", "Idea B"]
