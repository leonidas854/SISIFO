# Workflow: monografía

Versión corta del de tesis, para un trabajo de una asignatura.

```bash
taller nuevo mi-monografia --titulo "..." --entregable "salida/monografia.docx:docx:15"
taller buscar "tema" --fuentes openalex,crossref --n 20
taller descargar && taller extraer && taller indexar
taller consultar "pregunta concreta" 5
# escribir guion.json y afirmaciones.json
taller datos && taller bib --verificar && taller producir
taller verificar
```

Diferencias con la tesis: `minimo_referencias` sobre 15, sin `metodologia`
formal, y basta con `openalex,crossref`. El resto del proceso es idéntico —
en particular, las cifras siguen necesitando cita literal.
