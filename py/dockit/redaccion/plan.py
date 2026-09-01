"""El esquema del trabajo y los prompts que recibe el modelo local.

El modelo local redacta, pero no decide qué es verdad: se le entregan los
pasajes recuperados del índice y se le prohíbe salir de ahí. Todo lo que
escriba pasa después por `anclaje`, que descarta las citas no verificadas y
convierte las cifras en afirmaciones que hay que respaldar.
"""
from __future__ import annotations

import re

ESQUEMA_TESIS = [
    ("Introducción",
     "presenta el problema, por qué importa y qué responde el trabajo"),
    ("Planteamiento del problema",
     "delimita con precisión en qué consiste la dificultad"),
    ("Marco teórico",
     "los conceptos y definiciones que hacen falta para entender el resto"),
    ("Estado del arte",
     "qué soluciones existen hoy, con sus mecanismos y sus límites"),
    ("Análisis",
     "compara los enfoques y señala qué resuelve cada uno y a qué coste"),
    ("Riesgos y casos documentados",
     "qué ha fallado en la práctica y qué se aprendió"),
    ("Discusión",
     "qué queda abierto y qué compromisos hay que aceptar"),
    ("Conclusiones",
     "responde la pregunta del trabajo sin introducir material nuevo"),
]


def esquema_por_defecto(titulo: str) -> list[dict]:
    """Esquema de trabajo académico. El título orienta, no cambia la estructura."""
    return [{"titulo": t, "proposito": p} for t, p in ESQUEMA_TESIS]


def prompt_seccion(titulo: str, proposito: str, pasajes: list[dict],
                   idioma: str = "es", palabras: int = 320) -> str:
    """Prompt para redactar una sección anclada a los pasajes recuperados."""
    fuentes = "\n\n".join(
        f"[{p.get('fuente', '?')}] {p.get('texto', '').strip()}"
        for p in pasajes)
    lengua = "español" if idioma == "es" else idioma
    return f"""Eres un investigador redactando un trabajo académico en {lengua}.

FUENTES (lo único que puedes usar):
{fuentes}

TAREA: escribe el contenido de la sección «{titulo}».
Esa sección debe {proposito}.

REGLAS ESTRICTAS:
- Escribe el CONTENIDO, no describas lo que vas a escribir. Prohibido empezar
  con «Esta sección presenta…», «En este apartado se analizará…» o similares:
  entra directamente en la materia.
- Usa SOLO lo que dicen las fuentes. No inventes datos, cifras, fechas ni
  nombres que no aparezcan ahí.
- Cita SIEMPRE que tomes algo de una fuente, con su clave entre paréntesis tal
  como aparece entre corchetes. Ejemplo: (clave2020palabra). Un párrafo sin
  ninguna cita es un párrafo sin respaldo.
- No inventes claves: solo existen las de arriba.
- Si las fuentes no bastan, escribe menos. No rellenes.
- Prosa continua, sin viñetas, sin títulos, sin encabezados.
- Unas {palabras} palabras.

Texto de la sección:"""


def prompt_lamina(titulo: str, texto: str, maximo: int = 5) -> str:
    """Prompt para convertir una sección en viñetas de diapositiva."""
    return f"""Resume esta sección en viñetas para una diapositiva.

SECCIÓN: {titulo}
TEXTO:
{texto}

REGLAS:
- Máximo {maximo} viñetas.
- Cada viñeta, una idea completa de menos de 14 palabras.
- Sin citas ni claves entre paréntesis: van en el informe, no en la lámina.
- No inventes nada que no esté en el texto.
- Una viñeta por línea, sin numerar ni añadir guiones.

Viñetas:"""


# ── guion de diapositivas ────────────────────────────────────────────────

RE_VINETA = re.compile(r"^\s*(?:[-*•·]|\d+[.)])\s*")

# El modelo local antepone una frase de cortesía —«Aquí te presento las viñetas
# para la diapositiva:»— que acababa impresa como primera viñeta. Se reconoce
# por lo que es: una línea que ANUNCIA la lista en vez de formar parte de ella.
RE_PRELUDIO = re.compile(
    r"^(aqui|aquí|claro|por supuesto|a continuacion|a continuación|estas son|"
    r"estos son|te (dejo|presento|comparto)|resumen|vinetas|viñetas|ideas clave)"
    r"\b.*[:.]?\s*$",
    re.IGNORECASE)
RE_META = re.compile(r"\b(viñetas?|vinetas?|diapositiva)\b.*\b(para|de) la\b",
                     re.IGNORECASE)


def vinetas_desde(bruto: str, maximo: int = 5) -> list[str]:
    """Convierte la salida del modelo en viñetas limpias y acotadas.

    El modelo devuelve listas con guiones, números y a veces una frase de
    cortesía delante. El diseño de la lámina ya pone su propio marcador, así
    que aquí solo interesa el texto, y como mucho `maximo` ideas: una lámina
    con siete viñetas no se lee, se escanea.
    """
    salida: list[str] = []
    for linea in (bruto or "").splitlines():
        limpia = RE_VINETA.sub("", linea).strip()
        if not limpia or len(limpia) < 3:
            continue
        if RE_PRELUDIO.match(limpia) or RE_META.search(limpia):
            continue
        salida.append(limpia)
        if len(salida) >= maximo:
            break
    return salida


def guion_diapositivas(titulo: str, secciones: list[dict]) -> dict:
    """Arma el guion del .pptx siguiendo el índice del informe.

    Una lámina por sección, en el mismo orden: quien vea las diapositivas
    reconoce la estructura del trabajo escrito.
    """
    bloques: list[dict] = []
    for sec in secciones:
        vinetas = [v for v in (sec.get("vinetas") or []) if v]
        if not vinetas:
            continue
        bloques.append({"clase": "titulo", "nivel": 1, "texto": sec["titulo"]})
        bloques.append({"clase": "lista", "items": vinetas})
    return {"tipo": "pptx", "titulo": titulo, "autor": "", "bloques": bloques}
