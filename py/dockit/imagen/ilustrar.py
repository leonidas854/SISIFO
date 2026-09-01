"""De una diapositiva a su diagrama.

La imagen sale del texto de la propia lámina: los rótulos son sus viñetas y los
iconos se eligen por lo que dicen. Así no puede ilustrar otra cosa —que fue
justo el problema de las láminas anteriores, con iconos genéricos y sin letras
que no se relacionaban con nada.

Todo local y determinista: mismo texto, mismo diagrama, sin GPU ni modelo.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from . import diagramas

ANCHO, ALTO = 1600, 900

# Palabra clave -> icono del catálogo. El catálogo es del proyecto policial,
# así que aquí se aprovechan los que sirven para cualquier dominio.
SIGNIFICADOS: list[tuple[tuple[str, ...], str]] = [
    (("segur", "cifrad", "protec", "clave", "criptog", "integridad"), "candado"),
    (("extern", "global", "mundo", "internet", "red mundial", "internacional"), "mundo"),
    (("tiempo", "latencia", "demora", "plazo", "retardo", "frecuencia"), "reloj"),
    (("riesgo", "amenaza", "ataque", "vulnerab", "fallo", "problema", "peligro"), "alerta"),
    (("compar", "medic", "dato", "cifra", "estadist", "metric", "coste"), "barras"),
    (("analiz", "revis", "estudio", "examin", "auditor", "inspec"), "lupa"),
    (("traza", "custodia", "registro", "histor", "seguimiento", "cadena"), "trazabilidad"),
    (("central", "jerarq", "estructura", "capa", "nivel", "organiz"), "jerarquia"),
    (("descentral", "comunidad", "particip", "consenso", "colectiv", "usuarios"), "comunidad"),
    (("equilibr", "balance", "compromiso", "ventaja", "desventaja", "juicio"), "balanza"),
    (("norma", "ley", "regul", "legal", "marco", "contrato"), "libro_ley"),
    (("acuerdo", "comunic", "dialog", "interac", "mensaj", "solicitud"), "dialogo"),
    (("document", "informe", "archivo", "expediente", "fuente"), "carpeta"),
    (("verific", "valid", "comprob", "confian", "fiab", "garant"), "escudo_check"),
    (("mejor", "calidad", "destac", "import", "clave", "principal"), "estrella"),
    (("base", "fundament", "pilar", "soport", "infraestruct"), "columna"),
    (("observ", "monitor", "vigil", "supervis", "control"), "ojo"),
    (("proceso", "flujo", "etapa", "paso", "fase"), "cinta"),
]

# Cuando nada encaja, se reparte entre estos: neutros y legibles.
NEUTROS = ["columna", "carpeta", "estrella", "dialogo", "cinta", "etiqueta",
           "mundo", "barras", "lupa", "jerarquia"]

ORDINALES = ("primero", "segundo", "tercero", "despues", "después", "luego",
             "finalmente", "por ultimo", "por último", "entonces", "inicio", "fin")
OPUESTOS = ("ventaja", "desventaja", "pero", "aunque", "frente a", "mientras",
            "en cambio", "sin embargo", "riesgo", "beneficio")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s).lower())
    return s.encode("ascii", "ignore").decode()


def iconos_para(vinetas: list[str]) -> list[str]:
    """Un icono por viñeta, elegido por lo que dice y sin repetir."""
    elegidos: list[str] = []
    usados: set[str] = set()
    for i, vineta in enumerate(vinetas):
        texto = _norm(vineta)
        icono = next((nombre for claves, nombre in SIGNIFICADOS
                      if any(c in texto for c in claves) and nombre not in usados),
                     None)
        if icono is None:
            icono = next((n for n in NEUTROS if n not in usados), None)
        if icono is None:  # catálogo agotado: se repite antes que fallar
            icono = NEUTROS[i % len(NEUTROS)]
        elegidos.append(icono)
        usados.add(icono)
    return elegidos


def arquetipo_para(vinetas: list[str]) -> str:
    """La forma del diagrama sigue a la forma del contenido."""
    junto = _norm(" · ".join(vinetas))
    if any(o in junto for o in ORDINALES):
        return "flujo"
    if len(vinetas) == 2 or any(o in junto for o in OPUESTOS):
        return "contraste"
    # «capas» dibuja anillos concéntricos y con cinco rótulos se encabalgan.
    # «fila» reparte en horizontal con el rótulo debajo: se lee siempre.
    return "fila"


def spec_para(titulo: str, vinetas: list[str],
              con_titulo: bool = True) -> dict | None:
    """Especificación del diagrama de una lámina, o None si no hay qué dibujar."""
    limpias = [v.strip() for v in (vinetas or []) if v and v.strip()]
    if not limpias:
        return None
    limpias = limpias[:5]
    tipo = arquetipo_para(limpias)
    iconos = iconos_para(limpias)
    spec = {"tipo": tipo, "iconos": iconos, "rotulos": limpias,
            # la lámina ya lleva el título arriba: repetirlo compite con él
            "titulo": titulo.strip() if con_titulo else "",
            "acento": [0]}

    # «contraste» enfrenta dos bloques y pide otra forma de spec
    if tipo == "contraste":
        mitad = max(1, len(iconos) // 2)
        spec["izquierda"] = iconos[:mitad]
        spec["derecha"] = iconos[mitad:] or iconos[:1]
        spec["acento"] = "izquierda"
    return spec


def ilustrar_lamina(titulo: str, vinetas: list[str], destino_dir: Path,
                    nombre: str) -> Path | None:
    """Dibuja el diagrama de una lámina y devuelve la ruta del PNG."""
    spec = spec_para(titulo, vinetas, con_titulo=False)
    if spec is None:
        return None
    destino_dir = Path(destino_dir)
    destino_dir.mkdir(parents=True, exist_ok=True)
    try:
        return diagramas.escribir(spec, destino_dir / nombre, ANCHO, ALTO)
    except (KeyError, OSError) as e:
        # No se silencia: si un arquetipo no puede dibujarse hay que saberlo,
        # y se cae a «fila», que funciona con cualquier número de elementos.
        print(f"  aviso: «{spec['tipo']}» falló ({e}); uso «fila»")
        spec["tipo"] = "fila"
        try:
            return diagramas.escribir(spec, destino_dir / nombre, ANCHO, ALTO)
        except Exception as e2:
            print(f"  aviso: no pude ilustrar «{titulo}»: {e2}")
            return None
