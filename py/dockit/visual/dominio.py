"""Reglas del contrato visual, sin dependencias de PowerPoint ni de modelos.

Una imagen bonita pero ajena al contenido es un fallo. Una lámina normativa
sin el número de la ley también. Estas reglas convierten ambos defectos en
hallazgos concretos antes de gastar GPU o insertar archivos en una entrega.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable


TIPOS = {
    "portada", "foto", "diagrama", "ley", "grafico", "proceso",
    "comparacion", "mapa", "cita", "tabla", "ninguno",
}
MOTORES = {
    "nativo", "vector", "web", "sdxl", "imagegen", "foto", "ninguno",
}
MOTORES_RASTER = {"web", "sdxl", "imagegen", "foto"}
TIPOS_INFORMATIVOS = {"ley", "grafico", "proceso", "comparacion", "tabla"}
RE_NORMA = re.compile(
    r"\b(?:ley|decreto|resoluci[oó]n|reglamento|c[oó]digo|constituci[oó]n|"
    r"art[ií]culo|norma|r\.?\s*d\.?|d\.?\s*s\.?)\b", re.I,
)
RE_TEXTO_EN_PROMPT = re.compile(
    r"\b(?:readable|legible|written|text|letters?|words?|title|caption|label|"
    r"texto|letras?|t[ií]tulo|r[oó]tulo|leyenda)\b", re.I,
)
RE_PROHIBIR_TEXTO = re.compile(
    r"\b(?:no text|without text|sin texto|no typography|without letters)\b", re.I,
)
RE_MARCADOR = re.compile(
    r"(?:\b(?:todo|tbd|lorem|ipsum|insertar|pendiente)\b|\[.+?\]|x{3,})", re.I,
)


def _lista(valor: Any) -> list[str]:
    if valor is None:
        return []
    if isinstance(valor, str):
        return [valor.strip()] if valor.strip() else []
    if isinstance(valor, Iterable) and not isinstance(valor, (dict, bytes)):
        return [str(v).strip() for v in valor if str(v).strip()]
    return []


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = texto.encode("ascii", "ignore").decode().lower()
    return " ".join(re.findall(r"[a-z0-9]+", texto))


@dataclass(frozen=True)
class Procedencia:
    tipo: str = ""
    referencia: str = ""
    url: str = ""
    licencia: str = ""
    verificada: bool = False

    @classmethod
    def desde(cls, valor: Any) -> "Procedencia":
        if isinstance(valor, str):
            return cls(referencia=valor)
        if not isinstance(valor, dict):
            return cls()
        return cls(
            tipo=str(valor.get("tipo") or valor.get("kind") or "").strip().lower(),
            referencia=str(
                valor.get("referencia") or valor.get("cita")
                or valor.get("citation") or valor.get("id") or ""
            ).strip(),
            url=str(valor.get("url") or valor.get("uri") or "").strip(),
            licencia=str(valor.get("licencia") or valor.get("license") or "").strip(),
            verificada=bool(valor.get("verificada") or valor.get("verified")),
        )

    def declarada(self) -> bool:
        return bool(self.referencia or self.url)


@dataclass(frozen=True)
class Visual:
    diapositiva: int
    opcion: int
    titulo: str
    proposito: str
    tipo: str
    motor: str
    concepto_visual: str = ""
    conceptos: tuple[str, ...] = ()
    texto_visible: tuple[str, ...] = ()
    texto_alternativo: str = ""
    prompt: str = ""
    procedencia: Procedencia = field(default_factory=Procedencia)
    datos: dict[str, Any] = field(default_factory=dict)
    legado: bool = False

    @classmethod
    def desde(cls, bruto: dict[str, Any], *, legado: bool = False) -> "Visual":
        motor = str(bruto.get("motor") or bruto.get("engine") or "").strip().lower()
        tipo = str(bruto.get("tipo") or bruto.get("kind") or "").strip().lower()
        if legado:
            spec = bruto.get("spec") if isinstance(bruto.get("spec"), dict) else {}
            tipo = tipo if tipo in TIPOS else ("diagrama" if motor == "vector" else "foto")
            conceptos = _lista(bruto.get("conceptos"))
            if not conceptos:
                conceptos = _lista(spec.get("etiquetas"))
            concepto_visual = str(bruto.get("concepto_visual") or "").strip()
        else:
            conceptos = _lista(bruto.get("conceptos") or bruto.get("concepts"))
            concepto_visual = str(
                bruto.get("concepto_visual") or bruto.get("visual_concept") or ""
            ).strip()

        return cls(
            diapositiva=int(bruto.get("diapositiva") or bruto.get("slide") or 0),
            opcion=int(bruto.get("opcion") or bruto.get("option") or 1),
            titulo=str(bruto.get("titulo") or bruto.get("title") or "").strip(),
            proposito=str(
                bruto.get("proposito") or bruto.get("purpose")
                or bruto.get("que_debe_leerse") or ""
            ).strip(),
            tipo=tipo,
            motor=motor,
            concepto_visual=concepto_visual,
            conceptos=tuple(conceptos),
            texto_visible=tuple(_lista(
                bruto.get("texto_visible") or bruto.get("visible_text")
            )),
            texto_alternativo=str(
                bruto.get("texto_alternativo") or bruto.get("alt_text") or ""
            ).strip(),
            prompt=str(bruto.get("prompt_final") or bruto.get("prompt") or "").strip(),
            procedencia=Procedencia.desde(
                bruto.get("procedencia") or bruto.get("fuente") or bruto.get("source")
            ),
            datos=dict(bruto.get("datos") or bruto.get("data") or {}),
            legado=legado,
        )

    @property
    def clave(self) -> tuple[int, int]:
        return self.diapositiva, self.opcion

    @property
    def es_normativa(self) -> bool:
        return self.tipo == "ley" or bool(RE_NORMA.search(f"{self.titulo} {self.proposito}"))

    @property
    def texto_semantico(self) -> str:
        return " ".join((self.concepto_visual, *self.conceptos, self.prompt)).strip()


@dataclass(frozen=True)
class PlanVisual:
    version: int
    titulo: str
    visuales: tuple[Visual, ...]
    ruta: Path | None = None
    formato_legado: bool = False

    def por_diapositiva(self) -> dict[int, list[Visual]]:
        salida: dict[int, list[Visual]] = {}
        for visual in self.visuales:
            salida.setdefault(visual.diapositiva, []).append(visual)
        return salida


@dataclass(frozen=True)
class Hallazgo:
    codigo: str
    severidad: str
    mensaje: str
    accion: str
    diapositiva: int | None = None
    opcion: int | None = None
    archivo: str = ""

    def como_dict(self) -> dict[str, Any]:
        return {
            "codigo": self.codigo,
            "severidad": self.severidad,
            "diapositiva": self.diapositiva,
            "opcion": self.opcion,
            "archivo": self.archivo or None,
            "mensaje": self.mensaje,
            "accion": self.accion,
        }


def cargar_plan(ruta: str | Path) -> PlanVisual:
    ruta = Path(ruta)
    bruto = json.loads(ruta.read_text(encoding="utf-8"))
    if isinstance(bruto, list):
        items, legado, version, titulo = bruto, False, 1, ""
    elif isinstance(bruto, dict) and "trabajos" in bruto:
        items = bruto.get("trabajos") or []
        legado, version = True, int(bruto.get("version") or 0)
        titulo = str(bruto.get("titulo_tema") or bruto.get("titulo") or "")
    elif isinstance(bruto, dict):
        items = bruto.get("visuales") or bruto.get("slides") or []
        legado, version = False, int(bruto.get("version") or 1)
        titulo = str(bruto.get("titulo") or bruto.get("title") or "")
    else:
        raise ValueError("el plan visual debe ser un objeto o una lista JSON")
    if not isinstance(items, list):
        raise ValueError("visuales/slides/trabajos debe ser una lista")
    return PlanVisual(
        version=version,
        titulo=titulo.strip(),
        visuales=tuple(Visual.desde(i, legado=legado) for i in items if isinstance(i, dict)),
        ruta=ruta,
        formato_legado=legado,
    )


def _h(
    codigo: str, severidad: str, visual: Visual | None, mensaje: str, accion: str,
) -> Hallazgo:
    return Hallazgo(
        codigo, severidad, mensaje, accion,
        visual.diapositiva if visual else None,
        visual.opcion if visual else None,
    )


def validar_plan(
    plan: PlanVisual,
    similitudes: dict[tuple[int, int], float] | None = None,
    *,
    umbral_semantico: float = 0.48,
) -> list[Hallazgo]:
    """Valida cobertura, contenido legible, procedencia y coherencia semántica.

    ``similitudes`` llega desde un puerto semántico (bge-m3 o una alternativa
    determinista). El dominio solo aplica el umbral y no conoce el proveedor.
    """
    hallazgos: list[Hallazgo] = []
    if not plan.visuales:
        return [_h(
            "VIS-001", "error", None, "el plan visual está vacío",
            "declara al menos una visual por diapositiva de contenido",
        )]
    if plan.formato_legado:
        hallazgos.append(_h(
            "VIS-002", "aviso", None,
            "el plan usa el formato legado; no declara todos los contratos de accesibilidad y procedencia",
            "migra a plan_visual.json versión 1 con `sisifo visual migrar`",
        ))

    vistas: set[tuple[int, int]] = set()
    conceptos_vistos: dict[str, Visual] = {}
    for v in plan.visuales:
        if v.clave in vistas:
            hallazgos.append(_h(
                "VIS-003", "error", v, "diapositiva y opción repetidas",
                "usa una combinación (diapositiva, opción) única",
            ))
        vistas.add(v.clave)

        if v.diapositiva < 1:
            hallazgos.append(_h(
                "VIS-004", "error", v, "número de diapositiva inválido",
                "usa números de diapositiva desde 1",
            ))
        if not v.titulo:
            hallazgos.append(_h(
                "VIS-005", "error", v, "la visual no tiene título de diapositiva",
                "copia el título real de la diapositiva",
            ))
        elif RE_MARCADOR.search(v.titulo):
            hallazgos.append(_h(
                "VIS-006", "error", v, f"el título parece un marcador: «{v.titulo}»",
                "reemplázalo por el título definitivo",
            ))
        if len(v.proposito.split()) < 5:
            hallazgos.append(_h(
                "VIS-007", "error", v, "falta explicar qué debe entenderse al mirar la visual",
                "escribe una oración concreta en `proposito`",
            ))
        if v.tipo not in TIPOS:
            hallazgos.append(_h(
                "VIS-008", "error", v, f"tipo visual desconocido: «{v.tipo or '(vacío)'}»",
                f"usa uno de: {', '.join(sorted(TIPOS))}",
            ))
        if v.motor not in MOTORES:
            hallazgos.append(_h(
                "VIS-009", "error", v, f"motor visual desconocido: «{v.motor or '(vacío)'}»",
                f"usa uno de: {', '.join(sorted(MOTORES))}",
            ))
        if v.tipo != "ninguno" and not v.concepto_visual:
            hallazgos.append(_h(
                "VIS-010", "error", v, "falta describir la composición visual concreta",
                "añade `concepto_visual`; no repitas solamente el título",
            ))
        if v.tipo != "ninguno" and len(v.conceptos) < 2:
            hallazgos.append(_h(
                "VIS-011", "aviso", v, "hay menos de dos conceptos de aceptación explícitos",
                "añade los objetos/relaciones que deben aparecer en `conceptos`",
            ))
        if v.tipo not in {"portada", "ninguno"} and not v.texto_alternativo:
            hallazgos.append(_h(
                "VIS-012", "error", v, "falta texto alternativo para accesibilidad y auditoría semántica",
                "describe en una oración lo que muestra y por qué está aquí",
            ))

        concepto_norm = normalizar(v.concepto_visual)
        if concepto_norm:
            if concepto_norm in conceptos_vistos:
                previa = conceptos_vistos[concepto_norm]
                hallazgos.append(_h(
                    "VIS-013", "aviso", v,
                    f"concepto visual repetido; ya aparece en la diapositiva {previa.diapositiva}",
                    "varía la composición o justifica una serie visual intencional",
                ))
            else:
                conceptos_vistos[concepto_norm] = v

        if v.es_normativa:
            if v.motor not in {"nativo", "vector"}:
                hallazgos.append(_h(
                    "VIS-020", "error", v,
                    "una norma no debe confiar su identificación a una imagen raster generativa",
                    "usa texto nativo o SVG y deja la IA solo para una ilustración secundaria",
                ))
            if not v.texto_visible:
                hallazgos.append(_h(
                    "VIS-021", "error", v,
                    "la lámina normativa no declara texto visible; quedará como un libro/ícono vacío",
                    "incluye número, nombre de la norma y la idea jurídica exacta en `texto_visible`",
                ))
            if not v.procedencia.declarada():
                hallazgos.append(_h(
                    "VIS-022", "error", v, "la norma no tiene fuente jurídica declarada",
                    "añade URL oficial o clave bibliográfica verificada en `procedencia`",
                ))

        if v.motor in MOTORES_RASTER:
            if not v.prompt and v.motor in {"sdxl", "imagegen"}:
                hallazgos.append(_h(
                    "VIS-030", "error", v, "el motor generativo no tiene prompt",
                    "redacta una escena concreta alineada con el propósito",
                ))
            if v.prompt and RE_TEXTO_EN_PROMPT.search(v.prompt) and not RE_PROHIBIR_TEXTO.search(v.prompt):
                hallazgos.append(_h(
                    "VIS-031", "error", v,
                    "el prompt parece pedir texto legible a un motor raster",
                    "genera solo la escena y coloca títulos/rótulos con texto nativo o SVG",
                ))
            if not v.procedencia.declarada() and v.motor in {"web", "foto"}:
                hallazgos.append(_h(
                    "VIS-032", "error", v, "la fotografía no declara origen ni licencia",
                    "registra URL, autor/licencia y fecha de consulta",
                ))

        if v.tipo == "grafico":
            if not v.datos.get("fuente") and not v.procedencia.declarada():
                hallazgos.append(_h(
                    "VIS-040", "error", v, "el gráfico no declara la fuente de sus datos",
                    "añade `datos.fuente`, unidad, periodo y campos usados",
                ))
            if not v.datos.get("unidad"):
                hallazgos.append(_h(
                    "VIS-041", "aviso", v, "el gráfico no declara unidad",
                    "indica unidad o declara explícitamente que son conteos",
                ))

        if similitudes is not None and v.tipo not in {"portada", "ninguno"}:
            puntuacion = similitudes.get(v.clave)
            if puntuacion is not None and puntuacion < umbral_semantico:
                hallazgos.append(_h(
                    "VIS-050", "error", v,
                    f"la visual tiene baja relación semántica con la idea de la diapositiva ({puntuacion:.0%})",
                    "cambia la composición/conceptos o explica mejor el propósito antes de generar",
                ))

    return hallazgos


def construir_plan_desde_guion(guion: dict[str, Any]) -> dict[str, Any]:
    """Crea un borrador explícito a partir de los títulos y sus bloques.

    No pretende decidir la semántica creativa: deja campos marcados para que
    sean completados, pero evita empezar desde una hoja vacía y nunca inventa
    una fuente.
    """
    titulo_general = str(guion.get("titulo") or "Presentación").strip()
    visuales: list[dict[str, Any]] = [{
        "diapositiva": 1,
        "opcion": 1,
        "titulo": titulo_general,
        "proposito": "Presentar el tema, su alcance y la identidad de la exposición.",
        "tipo": "portada",
        "motor": "nativo",
        "concepto_visual": "Portada tipográfica con un motivo vectorial relacionado con el tema.",
        "conceptos": [titulo_general, "alcance"],
        "texto_visible": [titulo_general],
        "texto_alternativo": "Portada de la presentación.",
        "procedencia": {},
    }]
    numero = 1
    actual: dict[str, Any] | None = None
    textos: list[str] = []
    clases: list[str] = []

    def cerrar() -> None:
        nonlocal actual, textos, clases, numero
        if actual is None:
            return
        numero += 1
        titulo = actual["texto"].strip()
        resumen = " ".join(textos).strip()
        if len(resumen) > 260:
            resumen = resumen[:257].rsplit(" ", 1)[0] + "…"
        normativo = bool(RE_NORMA.search(f"{titulo} {resumen}"))
        tipo = "ley" if normativo else ("grafico" if "tabla" in clases else "diagrama")
        visible = [titulo] if normativo else []
        visuales.append({
            "diapositiva": numero,
            "opcion": 1,
            "titulo": titulo,
            "proposito": resumen or "TODO: explicar qué debe comprenderse en esta diapositiva.",
            "tipo": tipo,
            "motor": "vector" if tipo in {"ley", "diagrama"} else "nativo",
            "concepto_visual": "TODO: describir objetos, relación y composición sin repetir el título.",
            "conceptos": [],
            "texto_visible": visible,
            "texto_alternativo": "",
            "procedencia": {},
            "datos": {},
        })
        actual, textos, clases = None, [], []

    for bloque in guion.get("bloques") or []:
        if not isinstance(bloque, dict):
            continue
        clase = bloque.get("clase")
        if clase == "titulo" and int(bloque.get("nivel") or 1) <= 2:
            cerrar()
            actual = bloque
        elif actual is not None:
            clases.append(str(clase))
            if clase in {"parrafo", "cita"}:
                textos.append(str(bloque.get("texto") or ""))
            elif clase == "lista":
                textos.extend(str(x) for x in bloque.get("items") or [])
            elif clase == "tabla":
                textos.append(str(bloque.get("leyenda") or "Datos de la sección"))
    cerrar()
    return {"version": 1, "titulo": titulo_general, "visuales": visuales}
