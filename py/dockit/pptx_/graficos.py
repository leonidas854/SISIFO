# -*- coding: utf-8 -*-
"""Gráficos: barras, dona, organigrama, línea de tiempo y escala.
Todo en la paleta de la plantilla. Los que llevan cifras inventadas se rotulan
siempre como esquema ilustrativo, para que nadie los lea como dato oficial."""
import math
import vector as V
from compose import UPI, tspan, wrap, text_w

NOTA = 'Esquema ilustrativo, no representa datos oficiales'

def _nota(W, H, texto=NOTA, fs=None):
    fs = fs or max(7.5, min(10, W*0.014))
    return tspan(W/2, H-fs*0.35, [texto], 'med', fs, V.GRIS)

def barras(datos, w_in, h_in, titulo=None, nota=NOTA, valores=False):
    """datos: [(etiqueta, valor), ...]"""
    W, H = w_in*UPI, h_in*UPI
    s = V.svg_open(W, H)
    top = 4
    if titulo:
        fst = min(15, H*0.13)
        s += tspan(W/2, top+fst, [titulo.upper()], 'bold', fst, V.OLIVA); top += fst*1.6
    bot = H - (16 if nota else 6)
    fse = max(8.5, min(12, W*0.016))
    base = bot - fse*1.9
    alto = base - top
    n = len(datos)
    paso = W/n
    bw = min(paso*0.52, W*0.11)
    mx = max(v for _, v in datos) or 1
    for i, (et, v) in enumerate(datos):
        cx = paso*i + paso/2
        bh = alto * (v/mx) * 0.92
        col = V.OLIVA if i % 2 == 0 else V.ORO
        s += (f'<rect x="{cx-bw/2:.1f}" y="{base-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
              f'rx="{min(5, bw*0.16):.1f}" fill="{col}"/>')
        if valores:
            s += tspan(cx, base-bh-fse*0.45, [str(v)], 'bold', fse*0.95, V.OLIVA)
        s += tspan(cx, base+fse*1.25, wrap(et, 'semi', fse, paso*0.96)[:2], 'semi', fse, V.VERDE)
    s += f'<path d="M4 {base:.1f} H{W-4:.1f}" stroke="{V.GRIS}" stroke-width="2"/>'
    if nota: s += _nota(W, H, nota)
    return s + '</svg>'

def dona(datos, w_in, h_in, titulo=None, nota=NOTA):
    """datos: [(etiqueta, valor), ...] -> anillo con leyenda a la derecha."""
    W, H = w_in*UPI, h_in*UPI
    s = V.svg_open(W, H)
    top = 4
    if titulo:
        fst = min(15, H*0.13)
        s += tspan(W/2, top+fst, [titulo.upper()], 'bold', fst, V.OLIVA); top += fst*1.5
    zona = H - top - (16 if nota else 6)
    R  = min(zona*0.46, W*0.20)
    cx, cy = W*0.24, top + zona/2
    tot = sum(v for _, v in datos) or 1
    cols = [V.OLIVA, V.ORO, V.VERDE, V.GRIS, '#A8AE86']
    ang = -90
    for i, (et, v) in enumerate(datos):
        barrido = 360*v/tot
        a0, a1 = math.radians(ang), math.radians(ang+barrido)
        x0, y0 = cx+R*math.cos(a0), cy+R*math.sin(a0)
        x1, y1 = cx+R*math.cos(a1), cy+R*math.sin(a1)
        grande = 1 if barrido > 180 else 0
        s += (f'<path d="M{cx:.1f} {cy:.1f} L{x0:.1f} {y0:.1f} '
              f'A{R:.1f} {R:.1f} 0 {grande} 1 {x1:.1f} {y1:.1f} Z" fill="{cols[i%len(cols)]}"/>')
        ang += barrido
    s += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R*0.55:.1f}" fill="#FFFFFF"/>'
    fs = max(8.5, min(12, W*0.015))
    ly = top + zona/2 - len(datos)*fs*0.85
    for i, (et, v) in enumerate(datos):
        y = ly + i*fs*1.9
        s += f'<rect x="{W*0.46:.1f}" y="{y-fs*0.8:.1f}" width="{fs:.1f}" height="{fs:.1f}" rx="2" fill="{cols[i%len(cols)]}"/>'
        s += tspan(W*0.46+fs*1.5, y, [f'{et} — {round(100*v/tot)}%'], 'semi', fs, V.OLIVA, anchor='start')
    if nota: s += _nota(W, H, nota)
    return s + '</svg>'

def organigrama(raiz, hijos, w_in, h_in, titulo=None):
    W, H = w_in*UPI, h_in*UPI
    s = V.svg_open(W, H)
    top = 4
    if titulo:
        fst = min(14, H*0.12)
        s += tspan(W/2, top+fst, [titulo.upper()], 'bold', fst, V.OLIVA); top += fst*1.5
    zona = H - top - 6
    hr = min(zona*0.30, 34)
    fsr = max(9, min(13, W*0.016))
    rw = min(W*0.88, max(W*0.34, text_w(raiz.upper(), 'bold', fsr) + fsr*2.4))
    while text_w(raiz.upper(), 'bold', fsr) > rw - fsr*1.6 and fsr > 7.5:
        fsr -= 0.4
    s += (f'<rect x="{(W-rw)/2:.1f}" y="{top:.1f}" width="{rw:.1f}" height="{hr:.1f}" rx="6" fill="{V.OLIVA}"/>')
    s += tspan(W/2, top+hr*0.64, [raiz.upper()], 'bold', fsr, '#FFFFFF')
    n = len(hijos)
    gap = W*0.02
    cw = (W - gap*(n-1))/n
    ytop = top + hr + zona*0.22
    ch = zona - hr - zona*0.22
    for i, h in enumerate(hijos):
        x = i*(cw+gap)
        s += (f'<rect x="{x:.1f}" y="{ytop:.1f}" width="{cw:.1f}" height="{ch:.1f}" rx="6" '
              f'fill="{V.SUAVE}" stroke="{V.ORO}" stroke-width="2"/>')
        fs = max(8.5, min(12, cw*0.085))
        ls = wrap(h, 'semi', fs, cw*0.88)[:3]
        s += tspan(x+cw/2, ytop+ch/2-(len(ls)-1)*fs*0.6+fs*0.35, ls, 'semi', fs, V.OLIVA)
        cx = x+cw/2
        s += (f'<path d="M{W/2:.1f} {top+hr:.1f} V{top+hr+zona*0.11:.1f} H{cx:.1f} V{ytop:.1f}" '
              f'fill="none" stroke="{V.GRIS}" stroke-width="2.5"/>')
    return s + '</svg>'

def linea_tiempo(hitos, w_in, h_in, titulo=None):
    """hitos: [(rotulo, detalle)] -> hitos sobre una línea horizontal."""
    W, H = w_in*UPI, h_in*UPI
    s = V.svg_open(W, H)
    top = 4
    if titulo:
        fst = min(14, H*0.13)
        s += tspan(W/2, top+fst, [titulo.upper()], 'bold', fst, V.OLIVA); top += fst*1.6
    zona = H - top - 6
    n = len(hitos)
    paso = W/n
    fsr = max(9, min(13, paso*0.115))
    fsd = fsr*0.82
    lr = [wrap(r.upper(), 'bold', fsr, paso*0.95)[:2] for r, _ in hitos]
    ld = [wrap(d, 'med', fsd, paso*0.95)[:3] if d else [] for _, d in hitos]
    arriba = max(len(x) for x in lr)*fsr*1.22 + fsr*0.7
    y = top + arriba + fsr*0.5
    y = min(y, top + zona - max((len(x) for x in ld), default=0)*fsd*1.22 - fsd*1.2)
    s += f'<path d="M{paso*0.5:.1f} {y:.1f} H{W-paso*0.5:.1f}" stroke="{V.ORO}" stroke-width="5" stroke-linecap="round"/>'
    for i, (rot, det) in enumerate(hitos):
        cx = paso*i + paso/2
        s += f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="{fsr*0.75:.1f}" fill="{V.OLIVA}"/>'
        s += f'<circle cx="{cx:.1f}" cy="{y:.1f}" r="{fsr*0.32:.1f}" fill="#FFFFFF"/>'
        s += tspan(cx, y - arriba + fsr*0.9, lr[i], 'bold', fsr, V.OLIVA)
        if ld[i]:
            s += tspan(cx, y+fsr*2.1, ld[i], 'med', fsd, V.VERDE)
    return s + '</svg>'

def escala(niveles, w_in, h_in, titulo=None):
    """niveles: [(rotulo, detalle)] de menor a mayor -> galones crecientes."""
    W, H = w_in*UPI, h_in*UPI
    s = V.svg_open(W, H)
    top = 4
    if titulo:
        fst = min(14, H*0.13)
        s += tspan(W/2, top+fst, [titulo.upper()], 'bold', fst, V.OLIVA); top += fst*1.6
    zona = H - top - 6
    n = len(niveles)
    gap = W*0.012
    cw = (W - gap*(n-1))/n
    for i, (rot, det) in enumerate(niveles):
        x = i*(cw+gap)
        alto = zona*(0.52 + 0.48*(i+1)/n)
        yb = top + zona
        col = V.ORO if i == n-1 else V.OLIVA
        op  = 0.55 + 0.45*(i+1)/n
        s += (f'<rect x="{x:.1f}" y="{yb-alto:.1f}" width="{cw:.1f}" height="{alto:.1f}" rx="6" '
              f'fill="{col}" opacity="{op:.2f}"/>')
        fs = max(8.5, min(12, cw*0.10))
        ls = wrap(rot.upper(), 'bold', fs, cw*0.88)[:2]
        s += tspan(x+cw/2, yb-alto+fs*1.5, ls, 'bold', fs, '#FFFFFF')
        if det:
            s += tspan(x+cw/2, yb-alto/2+fs*0.9, wrap(det,'med',fs*0.85,cw*0.88)[:3], 'med', fs*0.85, '#FFFFFF')
    return s + '</svg>'
