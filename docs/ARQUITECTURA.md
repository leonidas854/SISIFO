# Arquitectura

## El problema que resuelve

Producir trabajos académicos —hasta nivel tesis— donde **cada dato es
comprobable**: la bibliografía existe de verdad, cada cifra tiene una cita
literal localizable en su fuente, y "terminado" es algo que una máquina puede
verificar en vez de una impresión.

## Por qué hexagonal

El dominio (qué es un trabajo, cuándo una referencia es citable, cuándo una
afirmación tiene respaldo) **no puede depender** de que hoy usemos OpenAlex y
mañana otra API, o de que los `.docx` los genere `python-docx`. Esas son
decisiones reemplazables; las reglas no.

```
        ┌──────────── adaptadores de entrada ────────────┐
        │  CLI (cmd/taller)          [futuro: HTTP/TUI]  │
        └───────────────────┬────────────────────────────┘
                            ▼
        ┌──────────── casos de uso (internal/casos) ─────┐
        │  investigar · verificar · producir · entregar  │
        └───────────────────┬────────────────────────────┘
                            ▼
        ┌──────────── dominio (internal/dominio) ────────┐
        │  Trabajo · Referencia · Afirmacion · Fuente    │
        │  CERO dependencias externas. Solo reglas.      │
        └───────────────────┬────────────────────────────┘
                            ▼
        ┌──────────── puertos (internal/puertos) ────────┐
        │  interfaces que el dominio necesita            │
        └───────────────────┬────────────────────────────┘
                            ▼
        ┌──────── adaptadores de salida (adaptadores/) ──┐
        │  openalex crossref datacite doaj arxiv         │
        │  ollama(bge-m3) · pythonproc · ficheros        │
        └────────────────────────────────────────────────┘
```

La regla de dependencia es una sola: **las flechas apuntan hacia dentro.**
`dominio` no importa nada de `adaptadores`. Si algún día se cambia OpenAlex por
otra cosa, se escribe otro adaptador y el dominio ni se entera.

## Los puertos

| Puerto | Qué promete | Adaptadores hoy |
|---|---|---|
| `BuscadorAcademico` | dado un tema, referencias reales con identificador | openalex, crossref, doaj, arxiv, europepmc |
| `VerificadorDOI` | dado un DOI, si existe y de qué trabajo es | crossref, datacite |
| `ExtractorTexto` | dado un documento, su texto | pdftotext, pypdf |
| `Indice` | dada una pregunta, los pasajes que la responden | ollama + bge-m3 |
| `GeneradorDocumento` | dado un guion, un .docx/.pptx/.xlsx | python-docx, python-pptx, openpyxl |
| `GeneradorImagen` | dada una intención, una imagen | sdxl local, vectorial |

## Reparto de lenguajes

Ni por moda ni por gusto: cada uno donde gana.

| | Dónde | Por qué |
|---|---|---|
| **Go** | dominio, casos de uso, CLI, índice, adaptadores HTTP | un binario sin runtime, arranque en milisegundos, concurrencia para hablar con cinco APIs a la vez. El dominio compila y se testea en 2 s |
| **Python** | generación de documentos y modelos | `python-docx`, `python-pptx`, `openpyxl`, `torch` no tienen equivalente serio en Go. Se invoca como adaptador, detrás de un puerto |
| **Rust** | *no se usa* | Go ya cubre la concurrencia y el binario único; Python cubre documentos y ML. Meter Rust hoy sería añadir una toolchain y un lenguaje sin ganar nada. Si algún día el troceado e indexado de decenas de miles de PDF se vuelve el cuello de botella, ese es su sitio |

El puente con Python es un puerto (`pythonproc`), no llamadas sueltas: recibe un
guion en JSON y devuelve un resultado en JSON. Eso permite testear el dominio sin
Python delante, y cambiar el generador sin tocar nada más.

## El guion de documento

La pieza que hace posible generar `.docx`, `.pptx` y `.xlsx` **sin duplicar
lógica**: los tres se describen con la misma estructura, y cada generador la
interpreta a su manera.

```json
{"tipo": "docx",
 "titulo": "…",
 "bloques": [
   {"clase": "titulo",    "nivel": 1, "texto": "Introducción"},
   {"clase": "parrafo",   "texto": "…", "citas": ["nath2024digital"]},
   {"clase": "tabla",     "cabecera": [...], "filas": [[...]], "leyenda": "…"},
   {"clase": "figura",    "ruta": "…", "leyenda": "…", "fuente": "…"},
   {"clase": "bibliografia"}
 ]}
```

El mismo guion produce el informe, las diapositivas que lo resumen y la hoja de
cálculo con sus datos. Un bloque `parrafo` con `citas` inserta la cita en el
texto con el formato que dicta citeproc, nunca escrita a mano.

## Estados de verificación

Son del dominio, no de un adaptador:

| Estado | Citable | Significa |
|---|---|---|
| `Verificada` | sí | el DOI resuelve y el título coincide |
| `SinDOI` | solo tras confirmación manual | libro, norma, informe |
| `NoExiste` | **no** | el DOI no está en ningún registro |
| `NoCoincide` | **no** | el DOI es de otro trabajo |
| `NoVerificada` | **no** | todavía no se comprobó |

## Cómo evoluciona

Añadir una fuente académica = un adaptador nuevo que cumpla `BuscadorAcademico`.
Añadir un formato de salida = un generador que interprete el guion. Nada de eso
toca el dominio, y por eso un cambio no se propaga a todos los trabajos.

## Orden de trabajo

Los tests van primero. El dominio no admite código sin test que lo justifique,
porque es donde viven las reglas que impiden publicar un dato inventado.
