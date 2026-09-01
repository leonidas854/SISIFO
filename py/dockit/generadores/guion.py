"""El guion: describe un documento sin comprometerse con el formato.

El mismo guion produce el informe, las diapositivas y la hoja de cálculo. Cada
generador lo interpreta a su manera, pero la validación es una sola y vive aquí.
"""
from __future__ import annotations

CLASES = {"titulo", "parrafo", "lista", "tabla", "figura", "cita",
          "salto", "bibliografia"}
TIPOS = {"docx", "pptx", "xlsx", "md"}


class GuionInvalido(ValueError):
    """El guion no describe un documento que se pueda producir."""


def _validar_bloque(b: dict, i: int) -> None:
    clase = b.get("clase")
    donde = f"bloque {i + 1}"
    if clase not in CLASES:
        raise GuionInvalido(f"{donde}: clase de bloque desconocida: {clase!r}")

    if clase == "titulo":
        if not b.get("texto"):
            raise GuionInvalido(f"{donde}: un título sin texto no sirve de nada")
        nivel = b.get("nivel", 0)
        if not isinstance(nivel, int) or not 1 <= nivel <= 6:
            raise GuionInvalido(f"{donde}: nivel de título fuera de rango: {nivel}")

    elif clase in ("parrafo", "cita"):
        if not b.get("texto"):
            raise GuionInvalido(f"{donde}: un bloque {clase} necesita texto")

    elif clase == "lista":
        if not b.get("items"):
            raise GuionInvalido(f"{donde}: una lista sin elementos")

    elif clase == "tabla":
        filas = b.get("filas") or []
        if not filas:
            raise GuionInvalido(f"{donde}: una tabla sin filas")
        cab = b.get("cabecera") or []
        if cab:
            for n, fila in enumerate(filas, 1):
                if len(fila) != len(cab):
                    raise GuionInvalido(
                        f"{donde}: la fila {n} tiene {len(fila)} celdas "
                        f"y la cabecera {len(cab)}")

    elif clase == "figura":
        if not b.get("ruta"):
            raise GuionInvalido(f"{donde}: una figura sin ruta de imagen")


def validar(guion: dict, disponibles: set[str] | None = None) -> None:
    """Comprueba el guion entero.

    `disponibles` son las claves de la bibliografía. Citar algo que no está ahí
    es exactamente el error que produce una referencia inventada, así que se
    rechaza al producir, no solo al verificar.
    """
    if guion.get("tipo") not in TIPOS:
        raise GuionInvalido(f"tipo de salida desconocido: {guion.get('tipo')!r}")
    if not guion.get("titulo"):
        raise GuionInvalido("el guion no tiene título")
    bloques = guion.get("bloques") or []
    if not bloques:
        raise GuionInvalido("el guion no tiene bloques")

    for i, b in enumerate(bloques):
        _validar_bloque(b, i)
        if disponibles is not None:
            for c in b.get("citas") or []:
                if c not in disponibles:
                    raise GuionInvalido(
                        f"bloque {i + 1} cita «{c}», que no está en la bibliografía")


def texto_con_citas(bloque: dict, en_texto: dict[str, str]) -> str:
    """Pega las citas al final de la frase, como manda APA.

    Se usa el texto que produjo citeproc, nunca uno escrito a mano: si no,
    el «et al.» y el orden de autores se desincronizan con la bibliografía.
    """
    texto = bloque.get("texto", "")
    claves = bloque.get("citas") or []
    if not claves:
        return texto
    citas = " ".join(en_texto.get(c, f"({c})") for c in claves)
    cuerpo = texto.rstrip()
    punto = cuerpo.endswith((".", "!", "?"))
    if punto:
        cuerpo = cuerpo[:-1].rstrip()
    return f"{cuerpo} {citas}." if punto else f"{cuerpo} {citas}"
