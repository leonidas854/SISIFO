---
# ─── Identidad ────────────────────────────────────────────────────────────
trabajo: SLUG
titulo: TITULO
materia: null
docente: null
entrega: null          # AAAA-MM-DD
idioma: es

# ─── Qué se entrega ───────────────────────────────────────────────────────
# Cada archivo que debe existir al final. verificar.py los comprueba uno a uno.
entregables:
  - archivo: salida/EJEMPLO.docx
    tipo: docx         # docx | pptx | pdf | md | otro
    minimo_paginas: null
    minimo_diapositivas: null

# ─── De dónde sale el contenido ───────────────────────────────────────────
fuentes:
  obligatorias: []     # rutas dentro de fuentes/ que SÍ o SÍ hay que usar
  web_permitida: false
  citas: obligatorias  # obligatorias | opcionales | no
  estilo_cita: APA

# ─── Investigación ────────────────────────────────────────────────────────
# Solo para trabajos con bibliografía. Rige buscar.py y afirmaciones.py.
investigacion:
  nivel: maestria          # licenciatura | maestria | doctorado
  pregunta: null           # la pregunta que el trabajo responde, en una frase
  fuentes_api: [openalex, crossref]   # openalex crossref doaj arxiv europepmc
  idiomas: [es, en]
  minimo_referencias: 20
  antiguedad_max_anios: null          # p.ej. 10 -> nada publicado antes
  metodologia: null        # revisión sistemática | estudio de caso | documental…
  criterios_inclusion: []  # qué entra: "revisado por pares", "sobre América Latina"
  criterios_exclusion: []  # qué se descarta y por qué

# ─── Cómo se ve ───────────────────────────────────────────────────────────
formato:
  tipografia: Calibri
  tamano_pt: 11
  margenes_cm: 2.5
  plantilla: null      # ruta a un .docx/.pptx cuyo estilo hay que respetar
  paleta: []           # colores institucionales, si los hay

# ─── Imágenes ─────────────────────────────────────────────────────────────
imagenes:
  usar: true
  origen: [vector]     # web | vector | sdxl | ninguno
  estilo: null         # "documental, realista, ambientado en Bolivia"
  prohibido: []        # lo que NUNCA debe aparecer en una imagen
  nota_obligatoria: null

# ─── Líneas rojas ─────────────────────────────────────────────────────────
# Se copian al principio de cada sesión. Si algo aquí se rompe, la entrega no vale.
prohibido:
  - inventar cifras o fechas
  - citar una referencia que no esté en fuentes/biblioteca.json
  - cambiar el texto literal de las fuentes

# ─── Criterio de terminado ────────────────────────────────────────────────
# Lo que hace que esto esté LISTO, no "casi". verificar.py lo lee y lo exige.
terminado:
  - todos los entregables existen y abren
  - toda cifra del texto tiene cita literal comprobada en la fuente
  - todas las referencias resuelven contra Crossref o DataCite
  - la bibliografía está en APA 7 generada por citeproc, no escrita a mano
  - revisado por mí de principio a fin
---

# TITULO

## Qué me están pidiendo

<!-- El enunciado literal del docente, pegado tal cual. No lo resumas: pégalo.
     Es lo primero que se te olvida contar y lo que más cambia el resultado. -->

## Qué quiero que salga

<!-- En una o dos frases: cómo se ve la entrega buena. Ej: "un informe de 10
     páginas que se pueda imprimir y leer sin proyector", "diapositivas para
     exponer en 15 minutos, poco texto y una imagen por idea". -->

## Contexto que no está en las fuentes

<!-- Lo que sabes tú y no está escrito en ningún archivo: qué espera el docente,
     qué pasó en clase, qué hicieron los otros equipos, qué te rebotaron antes. -->

## Decisiones ya tomadas

<!-- Se va llenando sobre la marcha. Cada vez que decidamos algo que no quieres
     volver a discutir, se anota aquí con la fecha. -->
