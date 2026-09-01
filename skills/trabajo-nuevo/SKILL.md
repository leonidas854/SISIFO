---
name: trabajo-nuevo
description: Arranca un trabajo académico o de investigación nuevo (informe, monografía, diapositivas, PDF para imprimir) capturando el contexto ANTES de producir nada. Úsala cuando el usuario diga que tiene un trabajo/práctica/entrega nueva, cuando pida "empezar" algo, o cuando pida un documento y no exista un BRIEF.md en la carpeta. También si un trabajo en curso resulta no tener BRIEF.md.
---

# Trabajo nuevo

El usuario produce documentos, diapositivas y PDF a partir de material de cátedra.
Su problema recurrente: **el contexto se le olvida contarlo**, y el trabajo sale a
medias porque nunca se definió qué era estar terminado.

Esta skill invierte eso: **tú preguntas, él no tiene que acordarse.**

## Regla de oro

No escribas ni una línea del entregable hasta que exista `BRIEF.md` con la cabecera
YAML llena. Si el usuario empuja para que empieces ya, haz el brief primero — son
dos minutos y evita rehacerlo entero.

## Paso 1 — Pregunta todo de una vez

Usa **una sola** llamada a `AskUserQuestion` con hasta 4 preguntas. Una tanda de
preguntas cuesta un turno; cuatro tandas cuestan cuatro. Prioriza, en este orden,
lo que más cambia el resultado:

1. **Qué se entrega**: formato y tamaño (informe de N páginas, N diapositivas, PDF
   para imprimir). Ofrece opciones concretas, no abiertas.
2. **De dónde sale el contenido**: ¿hay fuentes obligatorias de cátedra?, ¿se puede
   buscar en web?, ¿las citas son obligatorias?
3. **Cómo se ve**: ¿hay plantilla o normas institucionales que respetar?, ¿lleva
   imágenes y de qué tipo?
4. **Fecha de entrega**, si no la dijo.

Lo que el usuario ya te haya dicho en el mensaje, **no lo preguntes**.

Después pídele **el enunciado literal del docente** — pegado tal cual, sin resumir.
Es lo que más se olvida y lo que más cambia el resultado. Si no lo tiene a mano,
sigue, pero anótalo en el brief como pendiente.

## Paso 2 — Crea la carpeta

Una sola orden, sin escribir archivos a mano:

```bash
./taller nuevo <slug> --titulo "..." --materia "..." --entrega AAAA-MM-DD \
         --entregable "salida/informe.docx:docx:10" \
         --entregable "salida/diapos.pptx:pptx:15"
```

`./taller` está en la raíz de `tareas/` y es el único punto de entrada: no hay
que recordar rutas de scripts ni qué intérprete usar.

`--entregable` es `ruta:tipo[:mínimo]`, repetible. El mínimo es lo que convierte
"queda a medias" en un fallo detectable — ponlo siempre que sepas el tamaño pedido.

## Paso 3 — Termina de llenar el BRIEF

Edita `BRIEF.md` con lo que te contó:

- La cabecera YAML: `fuentes.obligatorias`, `imagenes`, `prohibido`, `terminado`.
- Las secciones en prosa: **Qué me están pidiendo** (el enunciado literal),
  **Qué quiero que salga**, **Contexto que no está en las fuentes**.

En `terminado:` escribe criterios **comprobables**, no deseos. Bien: "las 15
diapositivas tienen imagen", "toda cifra lleva fuente". Mal: "que quede bien".

En `prohibido:` recoge las líneas rojas del dominio. Si el trabajo es de la Policía
Boliviana, hereda las de `tareas/proyectos_policias/CLAUDE.md` (nada de heráldica
inventada, IA solo para objetos y lugares, leyenda obligatoria en gráficos con
cifras ilustrativas).

## Paso 4 — Dile qué poner en `fuentes/`

Termina indicándole que copie ahí el material de cátedra, y que cuando esté
avisará para indexarlo. No empieces a producir en el mismo turno: el brief se
revisa en frío.

## Reparto del trabajo

Prefiere siempre lo local, que no gasta tokens:

- extraer texto de PDF/pptx/docx → `docling` o `python-pptx`/`pypdf`
- indexar y recuperar → `bge-m3` por ollama
- imágenes → `sdxl-turbo` local o los generadores vectoriales del taller
- transcribir audio/video → `faster-whisper-large-v3`

Reserva el modelo para decidir qué va en cada sección y redactar.
