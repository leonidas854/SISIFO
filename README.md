# taller

Herramientas para producir trabajos académicos e investigación **verificable**:
documentos, diapositivas, PDF, audio y video, con bibliografía real y datos que
se pueden comprobar uno a uno.

Nace de once mil líneas escritas para trabajos concretos —ilustrar 238
diapositivas midiendo el hueco real de cada una, narrarlas, montarlas en video,
fusionar PDF para imprimir— que vivían dentro de cada proyecto y se perdían al
borrarlo. Aquí están centralizadas y son reutilizables.

## Por qué existe

Tres problemas concretos, y lo que hace cada pieza:

| Problema | Pieza |
|---|---|
| El trabajo queda a medias y "terminado" nunca se definió | `BRIEF.md` con criterio comprobable, y `taller verificar` que lo exige |
| Los modelos inventan referencias y cifras | toda referencia se busca (nunca se escribe) y todo dato lleva cita literal comprobada |
| Leer las fuentes cuesta carísimo | índice semántico local con `bge-m3`: se leen pasajes, no papers enteros |

## Instalación

Necesita Go 1.24+, Python 3.11+ y [ollama](https://ollama.com) con `bge-m3`.

```bash
git clone https://github.com/leonidas854/taller.git
cd taller && ./install.sh
taller doctor          # comprueba que no falte nada
```

`install.sh` compila el binario, prepara el intérprete, enlaza `taller` en
`~/.local/bin` y las skills en `~/.claude/skills`. **Todo apunta al repo**:
borrar una carpeta de trabajo no toca el sistema.

## Uso

```bash
taller nuevo mi-tesis --titulo "..." --entregable "salida/informe.docx:docx:40"
cd mi-tesis

taller buscar "tu tema" --fuentes openalex,crossref --n 30
taller descargar             # los PDF de acceso abierto
taller extraer               # PDF -> texto
taller indexar               # índice semántico local
taller consultar "¿qué dice la literatura sobre X?"

taller datos                 # ¿cada afirmación tiene respaldo?
taller bib --verificar       # bibliografía APA 7, cada DOI comprobado
taller producir --tipo docx,pptx,xlsx   # los entregables, desde un solo guion
taller verificar             # ¿está listo?

taller estado                # todos tus trabajos, estén donde estén
```

Funciona desde cualquier carpeta: encuentra el trabajo subiendo hasta el `BRIEF.md`.

## Las dos barreras contra el dato inventado

**Ninguna referencia se escribe: se busca.** `taller buscar` consulta OpenAlex,
Crossref, DOAJ, arXiv y Europe PMC —gratis, sin clave— y guarda CSL-JSON con DOI.
`taller bib --verificar` comprueba cada DOI contra **Crossref y, si no está,
DataCite**:

| Estado | Significa |
|---|---|
| `NO EXISTE` | el DOI no está en ningún registro — referencia inventada |
| `NO COINCIDE` | el DOI existe pero es de otro trabajo — la alucinación difícil de ver |
| `SIN-DOI` | puede ser legítimo (libro, norma, informe) — se verifica a mano |

**Ninguna cifra se afirma: se cita.** `afirmaciones.json` ancla cada dato a una
cita literal, y `taller datos` la busca en el texto de la fuente. Si no aparece,
falla: una frase inventada no sobrevive porque su cita no está en ningún documento.

El formato APA 7 lo produce citeproc-py con el estilo oficial CSL, no un modelo.

## Cómo está hecho

Go para lo que se beneficia de concurrencia y arranque instantáneo; Python para
documentos y modelos, donde están las bibliotecas que hacen falta.

```
cmd/taller/          CLI en Go: despacho, índice y consulta
internal/indice/     bge-m3 vía ollama, almacén gob, coseno por fuerza bruta
internal/trabajo/    localiza el motor, la carpeta activa y el registro
py/dockit/
  pptx_/             mide el hueco real de cada diapositiva y la ilustra
  imagen/            web, SDXL local, diagramas vectoriales, validación
  docx_/             documentos académicos (python-docx) y pptxgenjs
  pdf_/              n-up, recorte y fusión para imprimir
  medios/            narración por diapositiva y montaje de video
  texto/             extracción y orden de lectura de pptx
  verificar/         brief, búsqueda, bibliografía, afirmaciones
skills/              las skills de Claude Code, enlazadas a nivel de usuario
```

El índice no usa base de datos ni cgo: un fichero `gob` y coseno por fuerza
bruta. Para unos miles de fragmentos es instantáneo y no tiene nada que romperse.

## Un guion, tres formatos

`guion.json` describe el documento una sola vez y produce el informe, las
diapositivas y la hoja de cálculo:

```json
{"tipo": "docx", "titulo": "…", "bloques": [
  {"clase": "titulo",  "nivel": 1, "texto": "Introducción"},
  {"clase": "parrafo", "texto": "…", "citas": ["nath2024digital"]},
  {"clase": "tabla",   "cabecera": [...], "filas": [[...]], "leyenda": "Tabla 1. …"},
  {"clase": "bibliografia"}]}
```

Las citas se insertan con el texto que produce citeproc, nunca escrito a mano.
**Citar una clave no verificada hace fallar la generación**, no produce un
documento con una referencia dudosa dentro.

## Pruebas

```bash
make test      # 12 tests de dominio en Go + 24 de generación en Python
```

Las reglas del dominio —cuándo una referencia es citable, cuándo una afirmación
tiene respaldo, cuándo un trabajo está listo— se escribieron como tests antes
que como código.

## Estado

Funciona de punta a punta: búsqueda, descarga, extracción, índice, consulta
multilingüe, verificación de referencias y afirmaciones, bibliografía APA 7 y
generación de `.docx`, `.pptx` y `.xlsx`.

**Falta** exponer como órdenes de `taller` el canal de ilustración de
diapositivas y el de audio/video, que están en `py/dockit/` pero todavía atados
a los trabajos para los que se escribieron.

## Licencia

MIT
