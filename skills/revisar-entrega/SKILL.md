---
name: revisar-entrega
description: Comprueba si un trabajo (informe, monografía, diapositivas, PDF) está realmente terminado, contrastándolo contra su BRIEF.md, y arregla lo que falte. Úsala SIEMPRE antes de decirle al usuario que un entregable está listo, y cuando pregunte "¿está terminado?", "¿qué falta?", "revisa la entrega" o sospeche que algo quedó a medias.
---

# Revisar entrega

El usuario ha tenido entregas que parecían listas y no lo estaban. Esta skill
existe para que **nunca vuelvas a decir "listo" sin haberlo comprobado.**

## El ciclo

```bash
cd <carpeta-del-trabajo> && ../sisifo verificar
```

`taller` detecta solo sobre qué trabajo actúa: sube desde donde estés hasta
encontrar el `BRIEF.md`. Desde la raíz, `./sisifo estado` resume todos.

Sale con código 1 si algo automático falla. Añade `--rapido` para saltarte el
conteo real de páginas de los `.docx` (que convierte con LibreOffice y tarda);
úsalo mientras iteras, y haz la pasada completa antes de dar nada por cerrado.

1. **Ejecuta** el verificador.
2. **Arregla** lo que salga en `[ FALTA]`. Son fallos objetivos: el archivo no
   existe, está corto, no abre, no tiene citas, le falta la leyenda obligatoria.
3. **Vuelve a ejecutar.** Repite hasta que salga con 0 fallos.
4. **Reporta** al usuario los `[  ?   ]`: son las líneas rojas y el criterio de
   terminado, y solo él puede confirmarlos. Enúncialos como lo que son —
   pendientes de su revisión, no cosas que tú diste por buenas.

## Lo que no debes hacer

- **No declares terminado nada mientras el verificador dé código 1.** Si no puedes
  arreglar algo, dilo explícitamente y di por qué; no lo dejes pasar en silencio.
- **No bajes el listón del brief para que pase.** Si el brief pide 10 páginas y hay
  6, se escriben las 4 que faltan; no se edita `minimo_paginas` a 6. Cambiar el
  brief es decisión del usuario, y se le pregunta.
- **No confirmes tú los `[  ?   ]`.** "Revisado por mí" significa por él.

## Cuando falta contexto, no lo inventes

Si al arreglar descubres que el brief no dice algo que necesitas (qué fuente usar
para una cifra, qué va en una sección), **pregúntale y anota la respuesta en
`BRIEF.md`**, en la sección *Decisiones ya tomadas*, con la fecha. Así no se
vuelve a discutir ni se vuelve a olvidar.

## Verificación de contenido, no solo de forma

El verificador comprueba lo mecánico. Lo que solo puedes comprobar leyendo:

- **Cada cifra, fecha y nombre propio tiene que salir de una fuente de `fuentes/`.**
  Si no puedes señalar de dónde salió, no es un dato: es una alucinación, y se
  quita o se marca como estimación.
- **Las imágenes tienen que corresponder al contenido**, no ser decoración. Si la
  misma imagen serviría igual en otra sección, está mal elegida.
- **Nada de contenido de las fuentes reescrito** cuando el brief lo prohíbe: se
  cambia el formato, no las palabras.

## Reparto

Para revisar contenido a bajo coste, apóyate en local antes que en tokens:
`docling` para extraer el texto de las fuentes, `bge-m3` por ollama para buscar de
qué fuente salió una afirmación. Lee tú solo los pasajes que esa búsqueda devuelva,
no los documentos enteros.
