# -*- coding: utf-8 -*-
"""Deriva la consulta de imagen de cada diapositiva a partir de su título y su texto.
La tabla va de lo más específico a lo más general: gana la primera coincidencia."""
import re, unicodedata

def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

# (palabras clave, consulta de imagen, tipo sugerido)
#   tipo: 'foto' | 'grafico' | 'ia'
TABLA = [
 # --- Tema 3: prevención situacional ---
 (['iluminacion','alumbrado','entorno fisico','cptued','cpted'], 'alumbrado publico calle iluminada noche ciudad', 'foto'),
 (['control de acceso','acceso','reja','cerradura','porton'],    'control de acceso reja seguridad edificio', 'foto'),
 (['vigilancia','camara','videovigilancia','circuito cerrado'],  'camara de videovigilancia seguridad ciudadana', 'foto'),
 (['objetivo vulnerable','proteccion de objetivos'],             'policia resguardo banco comercio seguridad', 'foto'),
 (['coordinacion comunitaria','junta vecinal','vecinos'],        'reunion junta vecinal policia comunitaria', 'foto'),
 (['prevencion situacional','oportunidad delictiva'],            'patrullaje policial preventivo calle', 'foto'),
 # --- Tema 4: conflictos comunitarios ---
 (['mediacion','dialogo','facilitacion'],                        'mediacion policial dialogo vecinal conflicto', 'foto'),
 (['escucha activa'],                                            'policia escuchando ciudadano dialogo', 'foto'),
 (['des escalamiento','desescalamiento','tension'],              'policia calmando conflicto vecinal', 'foto'),
 (['negociacion'],                                               'negociacion policial mediacion partes', 'foto'),
 (['conflicto comunitario','conflicto vecinal','linderos'],      'conflicto vecinal discusion calle bolivia', 'foto'),
 # --- Tema 5: seguridad ciudadana ---
 (['estacion policial integral','epi'],                          'estacion policial integral EPI bolivia', 'foto'),
 (['policia comunitaria'],                                       'policia comunitaria bolivia barrio', 'foto'),
 (['brigada escolar'],                                           'brigada escolar de seguridad estudiantes', 'foto'),
 (['brigada de seguridad vecinal','seguridad vecinal'],          'brigada de seguridad vecinal bolivia', 'foto'),
 (['escuela de seguridad ciudadana'],                            'capacitacion seguridad ciudadana taller comunidad', 'foto'),
 (['observatorio'],                                              'estadisticas de seguridad ciudadana', 'grafico'),
 (['sistema nacional de seguridad','estructura del sistema'],    'organigrama sistema nacional seguridad ciudadana', 'grafico'),
 (['gacip','apoyo civil'],                                       'grupo de apoyo civil a la policia', 'foto'),
 # --- Tema 6: ética ---
 (['deontologia'],                                               'codigo de etica profesional libro', 'grafico'),
 (['codigo de etica'],                                           'codigo de etica policial documento', 'foto'),
 (['valores','honestidad','lealtad','disciplina','vocacion'],    'valores institucionales policia formacion', 'grafico'),
 (['principios policiales'],                                     'principios policiales servicio publico', 'grafico'),
 (['deberes'],                                                   'policia en formacion saludo institucional', 'foto'),
 (['moral','prudencia','coherencia','racionalidad'],             'etica y moral concepto balanza', 'grafico'),
 (['etica'],                                                     'etica policial servicio a la comunidad', 'foto'),
 # --- Tema 7: normativa internacional ---
 (['estambul'],                                                  'protocolo de estambul documentacion tortura', 'grafico'),
 (['minnesota'],                                                 'investigacion de muertes protocolo forense', 'foto'),
 (['bangkok'],                                                   'reglas de bangkok mujeres privadas de libertad', 'grafico'),
 (['nelson mandela'],                                            'reglas nelson mandela personas privadas libertad', 'grafico'),
 (['violencia de genero','ley 348','felcv'],                     'violencia de genero denuncia policia FELCV', 'foto'),
 (['racismo','discriminacion','ley 045'],                        'contra el racismo y la discriminacion campana', 'grafico'),
 (['trata','trafico de personas','ley 263'],                     'trata y trafico de personas prevencion', 'grafico'),
 (['codigo de conducta','naciones unidas','onu'],                'naciones unidas derechos humanos policia', 'foto'),
 (['derechos humanos'],                                          'derechos humanos policia capacitacion', 'foto'),
 # --- Tema 8: fijación del lugar del hecho ---
 (['fijacion fotografica','fotografia forense'],                 'fotografia forense escena del crimen camara', 'foto'),
 (['planimetrica','planimetria','croquis','plano'],              'croquis planimetrico escena del crimen dibujo', 'grafico'),
 (['audiovisual','video'],                                       'filmacion video escena del crimen policia', 'foto'),
 (['fijacion escrita','descripcion escrita'],                    'acta escrita policia redaccion informe', 'foto'),
 (['fijacion general'],                                          'vista general escena del crimen acordonada', 'foto'),
 (['fijacion detallada','primer plano'],                         'primer plano indicio testigo metrico forense', 'foto'),
 (['integridad de la escena','acordonamiento','preservar'],      'acordonamiento escena del crimen cinta policial', 'foto'),
 (['perito','criminalistica'],                                   'perito criminalistico trabajando escena', 'foto'),
 # --- Tema 10: información investigativa ---
 (['linea de tiempo','cronologic'],                              'linea de tiempo investigacion cronologia', 'grafico'),
 (['fuente de informacion','fuentes'],                           'fuentes de informacion investigacion policial', 'grafico'),
 (['informe preliminar','sistematizacion'],                      'redaccion informe policial escritorio', 'foto'),
 (['factores criminogenos'],                                     'analisis de factores criminogenos mapa', 'grafico'),
 (['clasificacion'],                                             'clasificacion y organizacion de informacion', 'grafico'),
 (['central de radio','transmision','comunicacion'],             'central de comunicaciones policial radio', 'foto'),
 # --- Tema 11: entrevistas ---
 (['entrevista','declaracion','entrevistado'],                   'toma de declaracion policial entrevista sala', 'foto'),
 (['victima','testigo'],                                         'policia entrevistando testigo victima', 'foto'),
 (['inconsistencia'],                                            'analisis de declaracion investigador notas', 'foto'),
 # --- Tema 12: etapa preparatoria ---
 (['etapa preparatoria','plazo','seis meses','duracion'],        'plazos del proceso penal calendario', 'grafico'),
 (['requerimiento conclusivo','resolucion conclusiva'],          'requerimiento fiscal documento juzgado', 'foto'),
 (['juez de instruccion','aviso al juez'],                       'juez de instruccion juzgado penal', 'foto'),
 (['ministerio publico','fiscal'],                               'fiscalia ministerio publico bolivia', 'foto'),
 (['investigacion paralela','investigaciones paralelas'],        'investigacion policial expediente carpeta', 'foto'),
 (['denuncia','querella','flagrancia','inicio'],                 'denuncia policial ventanilla ciudadano', 'foto'),
 # --- Tema 13: régimen disciplinario ---
 (['desercion'],                                                 'ausencia disciplinaria uniforme policial', 'foto'),
 (['falta leve','faltas leves'],                                 'faltas disciplinarias leves policia', 'grafico'),
 (['falta grave','faltas graves'],                               'faltas disciplinarias graves sancion', 'grafico'),
 (['sancion','arresto','destitucion','suspension'],              'sanciones disciplinarias escala', 'grafico'),
 (['tribunal disciplinario','tribunal','autoridad'],             'tribunal disciplinario audiencia policial', 'foto'),
 (['eximente','atenuante','agravante'],                          'balanza de la justicia atenuantes agravantes', 'grafico'),
 # --- Tema 14: corrupción ---
 (['enriquecimiento ilicito'],                                   'enriquecimiento ilicito investigacion patrimonial', 'grafico'),
 (['ley 004','marcelo quiroga'],                                 'ley marcelo quiroga santa cruz anticorrupcion', 'foto'),
 (['cohecho','soborno'],                                         'soborno dinero bajo la mesa corrupcion', 'foto'),
 (['peculado','malversacion'],                                   'malversacion de fondos publicos auditoria', 'grafico'),
 (['denuncia voluntaria'],                                       'denuncia anonima corrupcion buzon', 'foto'),
 (['codigo penal','tipo penal','delito'],                        'codigo penal boliviano libro justicia', 'foto'),
 (['corrupcion'],                                                'lucha contra la corrupcion transparencia', 'foto'),
 # --- genéricos de cierre ---
 (['registro','libro de novedades','documentar'],                'libro de novedades registro policial', 'foto'),
 (['supervision','evaluacion','impacto'],                        'supervision policial jefe evaluando', 'foto'),
 (['coordinacion interinstitucional'],                           'reunion interinstitucional autoridades mesa', 'foto'),
 (['patrullaje','servicio policial'],                            'patrullaje policial bolivia calle', 'foto'),
]

# Palabras demasiado generales: solo valen si aparecen en el TÍTULO.
GENERICAS = {'delito','policia','registro','codigo penal','denuncia','victima','testigo',
             'comunicacion','clasificacion','sancion','coordinacion interinstitucional'}

def _match(base, solo_titulo):
    for claves, q, tipo in TABLA:
        for k in claves:
            if norm(k) in base:
                if solo_titulo or norm(k) not in {norm(g) for g in GENERICAS}:
                    return q, tipo
    return None

def consulta(titulo, texto, tema=None):
    """Primero busca en el título (más específico); si no hay señal, en el cuerpo."""
    r = _match(norm(titulo), True)
    if r: return r
    r = _match(norm(f'{titulo} {texto}'), False)
    if r: return r
    t = norm(titulo).strip()
    return (f'policia boliviana {t[:45]}' if t else 'policia boliviana servicio'), 'foto'

if __name__ == '__main__':
    import json, sys
    d = json.load(open('todos_temas.json'))
    for k in sorted(d, key=int):
        if k == '9': continue
        print(f'== TEMA {k}')
        for s in d[k]['slides'][1:-1]:
            q, t = consulta(s['titulo'], s['texto'], k)
            print(f'  {s["n"]:2d} [{t:7s}] {q}')
