# Workflow: tesis

Para un trabajo largo con revisión de literatura, donde cada afirmación tiene
que aguantar que un tribunal la mire.

## 1. Definir

```bash
sisifo nuevo mi-tesis --titulo "..." \
      --entregable "salida/tesis.docx:docx:60" \
      --entregable "salida/defensa.pptx:pptx:20"
```

En el `BRIEF.md`, lo que más se olvida y más cambia el resultado:

```yaml
investigacion:
  nivel: maestria
  pregunta: "la pregunta que responde la tesis, en una frase"
  metodologia: revisión sistemática
  criterios_inclusion: ["revisado por pares", "posterior a 2015"]
  criterios_exclusion: ["sin metodología descrita"]
  minimo_referencias: 40
```

`criterios_inclusion` y `exclusion` no son burocracia: son lo que hace que la
búsqueda sea **reproducible** y lo que se escribe en el capítulo de método.

## 2. Investigar

```bash
sisifo buscar "tu tema en inglés" --fuentes openalex,crossref,doaj --n 40
sisifo buscar "tu tema en español" --fuentes openalex --idioma es --n 25
sisifo descargar          # los abiertos
sisifo extraer            # PDF -> texto
sisifo indexar            # una vez, tras extraer
```

`fuentes/busquedas.json` guarda cada consulta con su fecha: eso es el registro
que se cita en el método.

## 3. Leer sin arruinarse

```bash
sisifo consultar "¿qué se sabe de X?" 8
```

Lee **los pasajes**, no los PDF. De ahí salen las citas literales, ya copiadas
del texto real. Solo abre el documento entero cuando el pasaje se quede corto.

## 4. Anclar cada dato

Según escribes, cada afirmación con cifra entra en `afirmaciones.json`:

```json
{"id": "a12", "texto": "…", "fuente": "clave", "cita": "texto copiado", "localizador": "p. 12"}
```

```bash
sisifo datos       # falla si alguna cita no está en su fuente
```

## 5. Producir

```bash
sisifo bib --verificar    # comprueba cada DOI, saca APA 7 y las citas en texto
sisifo producir --tipo docx,pptx
```

El guion (`guion.json`) describe el documento una vez y produce el informe y la
defensa. **No se puede citar lo que no esté verificado**: el generador se planta.

## 6. Entregar

```bash
sisifo verificar          # sin --rapido: cuenta las páginas de verdad
```

Ábrelo en OnlyOffice, revísalo entero, y solo entonces confirma los criterios
manuales. El sistema nunca los da por buenos por su cuenta.
