---
name: investigacion
description: Investigación académica verificable de nivel maestría o doctorado — búsqueda en fuentes reales (OpenAlex, Crossref, DOAJ, arXiv, Europe PMC), bibliografía comprobada contra Crossref y DataCite, citas en APA 7 y afirmaciones ancladas a cita literal. Úsala cuando el usuario pida una investigación, monografía, tesis, estado del arte, marco teórico, bibliografía, o cuando pida datos "verificados", "reales" o "sin inventar".
---

# Investigación verificable

El usuario exige **datos reales, sin inventar**. Un modelo de lenguaje alucina
referencias con una facilidad enorme: DOI que no existen, autores atribuidos a
papers ajenos, cifras que suenan bien. Esta skill existe para que eso sea
**imposible de colar**, no para que "tengas cuidado".

## La regla que lo sostiene todo

**Solo puedes citar lo que está en `fuentes/biblioteca.json`.**
**Toda cifra necesita una cita literal que aparezca en el texto de la fuente.**

No escribas nunca una referencia de memoria. Si crees recordar un trabajo
relevante, búscalo con `buscar.py`: o aparece y entonces existe, o no aparece y
entonces no se cita.

## El ciclo

Todo desde dentro de la carpeta del trabajo, con el comando único:

```bash
cd <carpeta-del-trabajo>
T=../taller     # o ./taller si estás en la raíz de tareas/

# 1. buscar en fuentes reales — repetible, va acumulando y deduplicando
$T buscar "tu consulta" --fuentes openalex,crossref --n 25
$T buscar "la consulta en español" --fuentes openalex --idioma es

# 2. bajar los PDF abiertos y extraer su texto
$T descargar
$T extraer

# 3. comprobar que cada afirmación sale de una fuente
$T datos

# 4. verificar que las referencias existen y sacar la bibliografía APA 7
$T bib --verificar --locale es-ES
```

`taller` sabe qué trabajo es por el `BRIEF.md` y ya usa el intérprete correcto.

## Cómo se escribe con esto

Mientras redactas, **cada afirmación con dato entra en `afirmaciones.json`**:

```json
{"id": "a12",
 "texto": "La cadena de custodia documenta cada transferencia.",
 "fuente": "nath2024digital",
 "cita": "chain of custody documents every transfer",
 "localizador": "p. 12"}
```

`cita` es texto **copiado del documento**, no tu paráfrasis. El verificador lo
busca en `fuentes/textos/` y falla si no está. Si no puedes copiar una cita que
respalde la frase, la frase no se escribe.

Las afirmaciones sin cifra ni dato (hilo argumental, transiciones) no necesitan
entrada. Lo que lleve número, fecha, nombre propio o atribución, sí.

## Citar dentro del texto

`taller bib` deja en `fuentes/citas_en_texto.json` el mapa `clave -> "(Autor, año)"`,
producido por el mismo motor que la lista de referencias. **Úsalo literalmente**:
si escribes la cita a mano, el `et al.` y el orden de autores se desincronizan
con la bibliografía.

## Interpretación de los estados

| | Qué hacer |
|---|---|
| `NO EXISTE` | el DOI no está ni en Crossref ni en DataCite → la referencia se **elimina** |
| `NO COINCIDE` | el DOI es de otro trabajo → corregir el DOI o eliminar |
| `SIN-DOI` | puede ser legítimo (libro, informe, norma) → verificar a mano y anotarlo |
| `NO ESTÁ` | la cita no aparece en la fuente → **reescribir la frase** con lo que la fuente sí dice |
| `SIN FUENTE` | hay una cifra sin respaldo → buscarle fuente o quitarla |

Nunca ablandes el umbral ni borres la afirmación del JSON para que pase. El punto
del verificador es que no se pueda hacer trampa cómodamente.

## Ahorro de tokens: el índice

El cuello de botella es leer papers enteros. **No los leas.**

```bash
taller indexar                                   # una vez, tras extraer
taller consultar "¿qué dice la literatura sobre X?" 5
```

`taller indexar` trocea las fuentes y las embebe con `bge-m3` en local, coste
cero en tokens. `taller consultar` devuelve los pasajes más cercanos a tu
pregunta, con su fuente y su cercanía.

**Es multilingüe**: puedes preguntar en español sobre fuentes en inglés y las
encuentra igual. Úsalo siempre antes de abrir un PDF: lee los fragmentos, y solo
si se quedan cortos vas al documento completo.

De esos fragmentos salen las citas literales para `afirmaciones.json` — están
copiados del texto real, que es exactamente lo que el verificador exige.

`llama3.2` local sirve para tareas en lote sin criterio fino: clasificar si un
resumen es pertinente, agrupar por tema, detectar duplicados. No lo uses para
redactar ni para decidir qué se cita.

## Límites que debes declarar, no disimular

- **Acceso**: mucho de lo indexado es de pago. `_acceso_abierto` y `_pdf` en la
  biblioteca dicen qué puedes leer entero. De lo demás solo tienes el resumen, y
  una cita contra resumen es más débil — dilo en vez de fingir que leíste el
  artículo.
- **Cobertura**: OpenAlex y Crossref cubren mal la literatura gris local
  (normativa boliviana, tesis, informes institucionales). Eso lo aporta el
  usuario en `fuentes/`; pídeselo explícitamente en vez de sustituirlo por
  literatura internacional que no dice lo mismo.
- **DOI**: que un DOI resuelva prueba que el trabajo **existe**, no que sea bueno
  ni que diga lo que tú quieres que diga. La cita literal es lo que prueba eso.
