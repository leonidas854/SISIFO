from pathlib import Path
import os
# -*- coding: utf-8 -*-
"""Arma el plan completo: qué recibe cada diapositiva de cada tema.
Regla: foto si el concepto es fotografiable y no se repite; gráfico propio si el
título se repite dentro del tema (ahí la foto genérica no aporta); IA para escenas
concretas que el banco web no cubre."""
import json, os, glob, re
from consultas import consulta
import etiquetas as E

def _base_proyecto() -> str:
    """Carpeta del proyecto con los .pptx fuente.

    Se fija con TALLER_PROYECTO; si no, se busca subiendo desde donde se
    ejecuta. Nunca una ruta absoluta escrita a mano: el motor no puede depender
    de que exista una carpeta de trabajo concreta, porque se borran.
    """
    if _v := os.environ.get("TALLER_PROYECTO"):
        return str(Path(_v).resolve())
    _aqui = Path.cwd().resolve()
    for _c in [_aqui, *_aqui.parents]:
        if any(_c.glob("*DIAPOSITIVA*.pptx")) or (_c / "diapos_original").is_dir():
            return str(_c)
    return str(_aqui)


BASE = _base_proyecto()

# Temas donde el contenido es una lista de conceptos: mejor gráfico propio
FORZAR_GRAFICO = {
 '6':  list(range(10, 23)),   # valores, principios y deberes
 '7':  list(range(3, 11)),    # los 8 artículos del código de conducta
 '13': [4,5,6,7,8,9,10,11,12,13,14,17,18,19,20,21,22,23,24],
 '14': list(range(4, 22)),    # tipos penales
 '12': [3,4,9,10,11],
 '10': [7,8,9,10],
 '3':  [4,5,10,15],
 '4':  [3,5,7,8,14],
 '5':  [3,9],
 '11': [5,6,11,12],
 '8':  [11,12],
}

# Variantes para que dos diapositivas con el mismo prompt no salgan iguales
VARIANTES = [', wide angle', ', close up detail', ', from a low angle',
             ', overhead view', ', shallow depth of field', ', side view',
             ', early morning light', ', overcast light', ', warm interior light']

# Escenas seguras para IA: objetos y lugares, sin personas uniformadas ni insignias.
IA_PROMPTS = {
 'alumbrado publico calle iluminada noche ciudad':
   'a quiet residential street at night lit by warm streetlights, wet asphalt, empty sidewalk',
 'control de acceso reja seguridad edificio':
   'a metal security gate at the entrance of a residential building, daylight',
 'camara de videovigilancia seguridad ciudadana':
   'a modern security camera mounted on a pole above a city street, blue sky',
 'libro de novedades registro policial':
   'an open logbook with handwritten entries on a wooden desk, pen beside it',
 'redaccion informe policial escritorio':
   'a desk with an open folder, printed report pages, a pen and a desk lamp',
 'toma de declaracion policial entrevista sala':
   'an empty plain interview room with a table and two chairs, soft window light',
 'investigacion policial expediente carpeta':
   'stacked case folders and documents on an office desk, filing cabinet behind',
 'plazos del proceso penal calendario':
   'a wall calendar with several dates circled in red, on an office wall',
 'codigo penal boliviano libro justicia':
   'a thick law book closed on a desk next to a wooden gavel, warm light',
 'denuncia anonima corrupcion buzon':
   'a plain sealed suggestion box on a wall in an office corridor',
 'soborno dinero bajo la mesa corrupcion':
   'an envelope full of banknotes being passed under a wooden table, dim light',
 'acordonamiento escena del crimen cinta policial':
   'yellow barrier tape stretched across an empty street at dusk',
 'central de comunicaciones policial radio':
   'a dispatch room with radio equipment and monitors, no people, cool light',
 'estadisticas de seguridad ciudadana':
   'a printed bar chart report on a desk with a pen and reading glasses',
}

def construir():
    temas = json.load(open('todos_temas.json'))
    plan = {}
    for k in sorted(temas, key=int):
        if k == '9': continue
        d = temas[k]
        etq = E.resumen_deck(os.path.join(BASE, d['archivo']))
        usados = {}
        filas = []
        for s in d['slides']:
            n = s['n']
            if n == 1 or n == d['n']:            # portada y GRACIAS
                continue
            q, tipo = consulta(s['titulo'], s['texto'], k)
            conc = [c for c in etq.get(n, []) if not c.upper().startswith(('TEMA','SARGENTO','EXAMEN'))]
            if n in FORZAR_GRAFICO.get(k, []) and len(conc) >= 1:
                tipo = 'grafico'
            elif tipo == 'foto' and q in IA_PROMPTS and usados.get(q, 0) >= 1:
                tipo = 'ia'                       # repetida y es escena segura: la genera la IA
            elif tipo == 'foto' and usados.get(q, 0) >= 2:
                tipo = 'grafico' if conc else 'ia'
            usados[q] = usados.get(q, 0) + 1
            fila = dict(n=n, titulo=s['titulo'][:70], q=q, tipo=tipo, conceptos=conc)
            if tipo == 'ia':
                base_p = IA_PROMPTS.get(q, f'documentary scene related to {q}, no people')
                rep = sum(1 for f in filas if f.get('q') == q and f['tipo'] == 'ia')
                fila['prompt'] = base_p + VARIANTES[rep % len(VARIANTES)]
            filas.append(fila)
        plan[k] = filas
    json.dump(plan, open('plan_full.json','w'), ensure_ascii=False, indent=1)
    return plan

if __name__ == '__main__':
    p = construir()
    tot = {'foto':0,'grafico':0,'ia':0}
    for k, filas in p.items():
        c = {'foto':0,'grafico':0,'ia':0}
        for f in filas: c[f['tipo']] += 1; tot[f['tipo']] += 1
        print(f"TEMA {k:>2}: {len(filas):2d} diapos -> fotos {c['foto']:2d} | graficos {c['grafico']:2d} | IA {c['ia']:2d}")
    print('TOTAL:', sum(tot.values()), tot)
