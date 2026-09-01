# -*- coding: utf-8 -*-
"""Construye el gráfico de una diapositiva a partir de sus propios conceptos.
Elige el icono por palabra clave y arma tarjetas, escala o línea de tiempo."""
import re, unicodedata
import compose as C, vector as V, graficos as G

def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

ICONO = [
 (['honestidad','probidad','transparencia','integridad'], 'escudo_check'),
 (['lealtad','honor','patriotismo','bandera'],            'bandera'),
 (['disciplina','jerarquia','autoridad','subordinacion'], 'jerarquia'),
 (['vocacion','servicio','solidaridad','apoyo'],          'manos_apoyo'),
 (['dignidad','respeto','derechos humanos'],              'comunidad'),
 (['perseverancia','merito','distincion'],                'medalla'),
 (['justicia','legalidad','imparcialidad','equidad'],     'balanza'),
 (['profesionalidad','idoneidad','competencia'],          'estrella'),
 (['responsabilidad','deber','obligacion'],               'escudo_check'),
 (['tortura','trato cruel','fuerza','arma'],              'no_fuerza'),
 (['confidencial','reserva','secreto'],                   'candado'),
 (['salud','medica','atencion'],                          'botiquin'),
 (['corrupcion','soborno','cohecho','ilicito'],           'no_soborno'),
 (['fotografic','fotografia','camara'],                   'camara_foto'),
 (['planimetr','croquis','plano','dibujo'],               'croquis'),
 (['audiovisual','video','filmacion'],                    'video'),
 (['escrita','acta','informe','descripcion','registro'],  'formulario'),
 (['acordona','cinta','preservacion de la escena'],       'cinta'),
 (['plazo','duracion','termino','dias','meses'],          'reloj'),
 (['cronolog','linea de tiempo','fecha'],                 'calendario'),
 (['expediente','carpeta','cuaderno','archivo'],          'carpeta'),
 (['entrevista','declaracion','testigo','victima'],       'dialogo'),
 (['escucha','dialogo','comunicacion','diálogo'],         'dialogo'),
 (['vigilancia','patrullaje','observacion'],              'ojo'),
 (['iluminacion','alumbrado','luz'],                      'farola'),
 (['acceso','reja','barrera','cerco'],                    'reja'),
 (['camara de seguridad','videovigilancia','circuito'],   'camara_vig'),
 (['comunidad','vecinal','vecinos','ciudadan'],           'comunidad'),
 (['tribunal','juez','audiencia','instancia'],            'columna'),
 (['ley','codigo','norma','articulo','reglamento'],       'libro_ley'),
 (['internacional','naciones unidas','onu','protocolo'],  'mundo'),
 (['falta','sancion','infraccion','arresto'],             'alerta'),
 (['destitucion','desercion','baja'],                     'alerta'),
 (['prueba','evidencia','indicio'],                       'lupa'),
 (['laboratorio','pericia','analisis'],                   'matraz'),
 (['embalaje','bolsa','caja'],                            'caja_precinto'),
 (['traslado','transporte'],                              'camion'),
 (['bodega','almacen','deposito'],                        'estante'),
 (['estadistic','dato','indicador','porcentaje'],         'barras'),
 (['juicio','sentencia','condena'],                       'mazo'),
 (['huella','dactilar'],                                  'huella'),
 (['guante','manipulacion','recoleccion'],                'guante'),
 (['etiqueta','rotulo','codigo de identificacion'],       'etiqueta'),
 (['trazabilidad','seguimiento','historial'],             'trazabilidad'),
]

RESERVA = ['escudo_check','estrella','libro_ley','formulario','comunidad','balanza',
           'medalla','carpeta','columna','jerarquia','ojo','dialogo']

def icono_para(txt, defecto='escudo_check'):
    b = norm(txt)
    for claves, ic in ICONO:
        if any(norm(k) in b for k in claves):
            return ic
    return defecto

def iconos_distintos(textos):
    """Un icono por concepto, sin repetir dentro del mismo gráfico."""
    out, usados = [], set()
    for i, t in enumerate(textos):
        ic = icono_para(t, RESERVA[i % len(RESERVA)])
        if ic in usados:
            for alt in RESERVA:
                if alt not in usados:
                    ic = alt; break
        usados.add(ic); out.append(ic)
    return out

def limpiar(t):
    t = re.sub(r'^\s*[\dA-Za-z][\.\)\-•]\s*', '', t)
    t = re.sub(r'\s+', ' ', t).strip(' :.-–—•')
    return t

ANCHO_TARJETA = 2.0       # pulgadas mínimas por tarjeta para que el texto se lea
CORTO = 4                 # palabras máximas en el rótulo de una tarjeta

def _corto(c, n=CORTO):
    pal = c.split()
    return ' '.join(pal[:n]) + ('…' if len(pal) > n else '')

def grafico(conceptos, w_in, h_in, titulo=None, estilo='tarjetas'):
    cs = [limpiar(c) for c in conceptos if limpiar(c)]
    cs = [c for c in cs if len(c) >= 3]
    if not cs:
        return None
    cs.sort(key=lambda c: len(c))                 # los rótulos cortos leen mejor
    completos = [c for c in cs if len(c.split()) <= CORTO+1]
    cs = completos or [_corto(cs[0], 5)]
    cupo = max(1, int(w_in // ANCHO_TARJETA))
    cs = cs[:1] if (w_in < 4.0 or cupo == 1) else cs[:min(4, cupo)]
    if estilo == 'escala':
        return G.escala([(c, '') for c in cs], w_in, h_in, titulo)
    if estilo == 'tiempo':
        return G.linea_tiempo([(c, '') for c in cs], w_in, h_in, titulo)
    items = list(zip(iconos_distintos(cs), cs))
    if len(items) == 1:
        ic, lb = items[0]
        W, H = w_in*C.UPI, h_in*C.UPI
        s = V.svg_open(W, H)
        icp = min(H*0.62, W*0.20)
        fs  = max(11, min(20, W*0.030))
        ls  = C.wrap(lb.upper(), 'bold', fs, W*0.60)[:2]
        bh  = max(icp, len(ls)*fs*1.25)
        y0  = (H-bh)/2
        s += f'<g transform="translate({W*0.20-icp/2:.1f},{y0+(bh-icp)/2:.1f}) scale({icp/100:.4f})">{V.icon(ic)}</g>'
        s += C.tspan(W*0.34, y0+bh/2-(len(ls)-1)*fs*0.62+fs*0.34, ls, 'bold', fs, V.OLIVA, anchor='start')
        return s + '</svg>'
    return C.icon_row(items, w_in, h_in)
