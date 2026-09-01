# SISIFO

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
| El trabajo queda a medias y "terminado" nunca se definió | `BRIEF.md` con criterio comprobable, y `sisifo verificar` que lo exige |
| Los modelos inventan referencias y cifras | toda referencia se busca (nunca se escribe) y todo dato lleva cita literal comprobada |
| Leer las fuentes cuesta carísimo | índice semántico local con `bge-m3`: se leen pasajes, no papers enteros |

## Instalación

Necesita Go 1.24+, Python 3.11+ y [ollama](https://ollama.com) con `bge-m3`.

```bash
git clone https://github.com/leonidas854/taller.git
cd taller && ./install.sh
sisifo doctor          # comprueba que no falte nada
```

`install.sh` compila el binario, prepara el intérprete, enlaza `taller` en
`~/.local/bin` y las skills en `~/.claude/skills`. **Todo apunta al repo**:
borrar una carpeta de trabajo no toca el sistema.

## Uso

```bash
sisifo nuevo mi-tesis --titulo "..." --entregable "salida/informe.docx:docx:40"
cd mi-tesis

sisifo buscar "tu tema" --fuentes openalex,crossref --n 30
sisifo descargar             # los PDF de acceso abierto
sisifo extraer               # PDF -> texto
sisifo indexar               # índice semántico local
sisifo consultar "¿qué dice la literatura sobre X?"

sisifo datos                 # ¿cada afirmación tiene respaldo?
sisifo bib --verificar       # bibliografía APA 7, cada DOI comprobado
sisifo producir --tipo docx,pptx,xlsx   # los entregables, desde un solo guion
sisifo verificar             # ¿está listo?

sisifo estado                # todos tus trabajos, estén donde estén
```

Funciona desde cualquier carpeta: encuentra el trabajo subiendo hasta el `BRIEF.md`.

## Las dos barreras contra el dato inventado

**Ninguna referencia se escribe: se busca.** `sisifo buscar` consulta OpenAlex,
Crossref, DOAJ, arXiv y Europe PMC —gratis, sin clave— y guarda CSL-JSON con DOI.
`sisifo bib --verificar` comprueba cada DOI contra **Crossref y, si no está,
DataCite**:

| Estado | Significa |
|---|---|
| `NO EXISTE` | el DOI no está en ningún registro — referencia inventada |
| `NO COINCIDE` | el DOI existe pero es de otro trabajo — la alucinación difícil de ver |
| `SIN-DOI` | puede ser legítimo (libro, norma, informe) — se verifica a mano |

**Ninguna cifra se afirma: se cita.** `afirmaciones.json` ancla cada dato a una
cita literal, y `sisifo datos` la busca en el texto de la fuente. Si no aparece,
falla: una frase inventada no sobrevive porque su cita no está en ningún documento.

El formato APA 7 lo produce citeproc-py con el estilo oficial CSL, no un modelo.

## Cómo está hecho

Go para lo que se beneficia de concurrencia y arranque instantáneo; Python para
documentos y modelos, donde están las bibliotecas que hacen falta.

```
cmd/sisifo/          CLI en Go: despacho, índice y consulta
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

## Nada se pisa: variantes por pasada y por tema

Abres el entregable en OnlyOffice, lo retocas y lo usas. La siguiente pasada
**no lo destruye**:

```bash
sisifo producir --tipo pptx            # salida/informe.pptx
sisifo producir --tipo pptx            # salida/informe-v2.pptx   (no pisa)
sisifo producir --tipo pptx --variante tema3   # salida/informe-tema3.pptx
sisifo producir --tipo pptx --sobrescribir     # solo si lo pides
```

Así puedes tener unas diapositivas distintas en cada pasada, o una por cada
tema que vayas desarrollando, sin perder lo que ya revisaste a mano.

## Hojas de cálculo con identidad

Un Excel genérico se nota. Hay seis temas que difieren en color, trato de la
cabecera, bandas y bordes; cada trabajo recibe uno de forma estable —el mismo
trabajo sale siempre igual, trabajos distintos se ven distintos— y el BRIEF
puede imponer el suyo:

```bash
sisifo producir --tipo xlsx --estilo tecnico
sisifo producir --estilo '?'     # lista los temas
```

```yaml
formato:
  estilo: oliva      # en el BRIEF: manda sobre la elección automática
```

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

El PPTX se genera con **pptxgenjs** cuando hay Node: tablas y gráficos quedan
como objetos nativos y editables en PowerPoint, con notas del orador, en vez de
imágenes planas. Sin Node se usa python-pptx, que produce lo mismo salvo los
gráficos nativos. Forzar uno u otro: `SISIFO_PPTX=python`.

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
