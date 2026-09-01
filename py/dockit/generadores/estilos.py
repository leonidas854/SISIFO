"""Temas visuales para los entregables.

Un Excel genérico se nota: todos iguales, gris, sin jerarquía. Aquí viven
varias identidades distintas —no solo colores cambiados, también el trato de
la cabecera, las bandas y los bordes— para que dos trabajos no se confundan.

Si el usuario impone un estilo en el BRIEF (`formato.estilo`), ese manda.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Tema:
    nombre: str
    descripcion: str
    cabecera_fondo: str      # ARGB sin almohadilla
    cabecera_texto: str
    banda_fondo: str         # fila alterna; vacío = sin bandas
    acento: str
    texto: str
    bandas: bool
    cabecera_negrita: bool
    borde: str               # "fino" | "solo-cabecera" | "ninguno"
    fuente: str


TEMAS: dict[str, Tema] = {
    "sobrio": Tema(
        "sobrio", "gris institucional, sin bandas, borde fino",
        "E8ECEF", "1A1A1A", "", "40566B", "1A1A1A",
        bandas=False, cabecera_negrita=True, borde="fino", fuente="Calibri"),

    "academico": Tema(
        "academico", "azul apagado con bandas suaves, para tablas largas",
        "1F3864", "FFFFFF", "EDF1F7", "2E5FA3", "1A1A1A",
        bandas=True, cabecera_negrita=True, borde="solo-cabecera",
        fuente="Calibri"),

    "calido": Tema(
        "calido", "ocre y tierra, cabecera sin negrita, sin bordes",
        "C9A538", "2B2410", "FBF5E3", "8A6D1F", "2B2410",
        bandas=True, cabecera_negrita=False, borde="ninguno",
        fuente="Calibri"),

    "oliva": Tema(
        "oliva", "verde oliva institucional, borde fino, sin bandas",
        "455119", "FFFFFF", "", "5E672C", "1A1A1A",
        bandas=False, cabecera_negrita=True, borde="fino", fuente="Calibri"),

    "tecnico": Tema(
        "tecnico", "alto contraste y monoespaciada, para datos densos",
        "1A1A1A", "F2F2F2", "F5F5F5", "0E6C82", "1A1A1A",
        bandas=True, cabecera_negrita=True, borde="fino",
        fuente="Consolas"),

    "claro": Tema(
        "claro", "casi sin adorno, cabecera con línea de acento",
        "FFFFFF", "0E6C82", "FAFBFC", "0E6C82", "1A1A1A",
        bandas=True, cabecera_negrita=True, borde="solo-cabecera",
        fuente="Calibri"),
}

POR_DEFECTO = "sobrio"


def elegir(semilla: str, pedido: str | None = None) -> Tema:
    """Devuelve el tema a usar.

    `pedido` gana siempre: si el usuario fijó un estilo, no se le lleva la
    contraria. Si no, se reparte de forma estable a partir del nombre del
    trabajo: el mismo trabajo sale siempre igual, y trabajos distintos tienden
    a verse distintos.
    """
    if pedido:
        clave = str(pedido).strip().lower()
        if clave in TEMAS:
            return TEMAS[clave]
    if not semilla:
        return TEMAS[POR_DEFECTO]
    orden = sorted(TEMAS)
    h = hashlib.sha256(str(semilla).encode("utf-8")).digest()
    return TEMAS[orden[h[0] % len(orden)]]


def listar() -> list[tuple[str, str]]:
    return [(t.nombre, t.descripcion) for t in TEMAS.values()]
