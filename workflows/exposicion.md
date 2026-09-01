# Workflow: exposición

Cuando el documento ya está escrito y hacen falta las diapositivas.

```bash
cd <trabajo-existente>
sisifo producir --tipo pptx
```

El mismo `guion.json` que produjo el `.docx` produce el `.pptx`: una lámina por
título de nivel 1 o 2, con lo que cuelga de él resumido, máximo seis viñetas.

## Si las diapositivas son el entregable principal

Escribe el guion pensando en la lámina: títulos cortos, párrafos de una idea.
Un párrafo largo se recorta en la primera frase completa, así que si sale
truncado es señal de que la idea era demasiado densa para una diapositiva.

## Ilustrarlas

El canal que mide el hueco real de cada lámina y coloca una imagen está en
`py/dockit/pptx_` e `py/dockit/imagen`. Todavía no está expuesto como orden de
`taller`: hoy se usa desde su carpeta, como en `proyectos_policias`.
