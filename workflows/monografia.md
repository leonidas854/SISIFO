# Workflow: monografía

Versión corta del de tesis, para un trabajo de una asignatura.

```bash
sisifo nuevo mi-monografia --titulo "..." --entregable "salida/monografia.docx:docx:15"
sisifo buscar "tema" --fuentes openalex,crossref --n 20
sisifo descargar && sisifo extraer && sisifo indexar
sisifo consultar "pregunta concreta" 5
# escribir guion.json y afirmaciones.json
sisifo datos && sisifo bib --verificar && sisifo producir
sisifo verificar
```

Diferencias con la tesis: `minimo_referencias` sobre 15, sin `metodologia`
formal, y basta con `openalex,crossref`. El resto del proceso es idéntico —
en particular, las cifras siguen necesitando cita literal.
