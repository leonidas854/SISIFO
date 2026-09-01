# -*- coding: utf-8 -*-
"""Composers: arman gráficos completos (flujo, fila de iconos, rótulo) a partir de los iconos."""
from PIL import ImageFont
import vector as V

UPI   = 100                      # unidades SVG por pulgada
FONTS = {'bold':'fonts/Montserrat-Bold.ttf', 'semi':'fonts/Montserrat-SemiBold.ttf',
         'med':'fonts/Montserrat-Medium.ttf', 'reg':'fonts/Montserrat-Regular.ttf'}
_cache = {}

def _font(w, size):
    k = (w, int(size*4))
    if k not in _cache:
        _cache[k] = ImageFont.truetype(FONTS[w], int(size*4))
    return _cache[k]

def text_w(s, w, size):
    return _font(w, size).getlength(s) / 4.0

def wrap(s, w, size, maxw):
    words, lines, cur = s.split(), [], ''
    for word in words:
        t = (cur + ' ' + word).strip()
        if text_w(t, w, size) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = word
    if cur: lines.append(cur)
    return lines

def tspan(x, y, lines, w, size, fill, lh=1.22, anchor='middle'):
    out = ''
    for i, ln in enumerate(lines):
        out += (f'<text x="{x:.1f}" y="{y + i*size*lh:.1f}" font-family="Montserrat" '
                f'font-size="{size:.1f}" font-weight="{700 if w=="bold" else 600 if w=="semi" else 500}" '
                f'fill="{fill}" text-anchor="{anchor}">{V.esc(ln)}</text>')
    return out

def chevron(x, y, h, color=V.ORO):
    """Flecha tipo galón apuntando a la derecha, centrada en (x,y)."""
    return (f'<path d="M{x-h*0.28:.1f} {y-h*0.42:.1f} L{x+h*0.30:.1f} {y:.1f} '
            f'L{x-h*0.28:.1f} {y+h*0.42:.1f}" fill="none" stroke="{color}" '
            f'stroke-width="{h*0.20:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')

def flow(steps, w_in, h_in, title=None):
    """Flujo horizontal: [(icono, 'ETIQUETA'), ...] separados por galones dorados."""
    W, H = w_in*UPI, h_in*UPI
    s = V.svg_open(W, H)
    top = 4
    if title:
        fs = min(16, H*0.13)
        s += tspan(W/2, top+fs, [title.upper()], 'bold', fs, V.OLIVA)
        top += fs*1.5
    n   = len(steps)
    arw = W*0.030
    cw  = (W - arw*(n-1)) / n
    avail = H - top - 4
    fs  = max(9.5, min(13.5, cw*0.125))
    wrapped = [wrap(lb.upper(), 'semi', fs, cw*0.96)[:3] if lb else [] for _, lb in steps]
    maxln   = max((len(w) for w in wrapped), default=0)
    ic  = min(cw*0.46, (avail - maxln*fs*1.22 - (fs*0.5 if maxln else 0)) * 0.95)
    ic  = max(ic, avail*0.35)
    block = ic + (fs*1.15 + (maxln-1)*fs*1.22 if maxln else 0)
    y0    = top + max(0, (avail - block)/2)
    for i, (ico, _) in enumerate(steps):
        cx = i*(cw+arw) + cw/2
        s += (f'<g transform="translate({cx-ic/2:.1f},{y0:.1f}) scale({ic/100:.4f})">'
              f'{V.icon(ico)}</g>')
        if wrapped[i]:
            s += tspan(cx, y0+ic+fs*1.15, wrapped[i], 'semi', fs, V.OLIVA)
        if i < n-1:
            s += chevron(i*(cw+arw)+cw+arw/2, y0+ic/2, ic*0.42)
    return s + '</svg>'


def icon_row(items, w_in, h_in, card=True):
    """Fila de tarjetas: [(icono, 'TITULO', 'texto opcional'), ...]"""
    W, H = w_in*UPI, h_in*UPI
    s = V.svg_open(W, H)
    n   = len(items)
    gap = W*0.022
    cw  = (W - gap*(n-1)) / n
    pad = H*0.10
    fst = max(10, min(15, cw*0.085))
    fss = max(8.5, fst*0.80)
    tls = [wrap(it[1].upper(), 'bold', fst, cw*0.90)[:2] for it in items]
    sls = [wrap(it[2], 'med', fss, cw*0.90)[:3] if len(it) > 2 and it[2] else [] for it in items]
    maxt, maxs = max(len(t) for t in tls), max((len(x) for x in sls), default=0)
    avail = H - 2*pad
    txth  = maxt*fst*1.22 + (fss*0.6 + maxs*fss*1.22 if maxs else 0)
    ic    = min(cw*0.42, max((avail - txth)*0.92, avail*0.30))
    block = ic + fst*1.05 + txth - fst*0.17
    y0    = pad + max(0, (avail - block)/2)
    for i, it in enumerate(items):
        x = i*(cw+gap)
        if card:
            s += (f'<rect x="{x:.1f}" y="0" width="{cw:.1f}" height="{H:.1f}" rx="{H*0.10:.1f}" '
                  f'fill="{V.SUAVE}" stroke="{V.GRIS}" stroke-opacity="0.45" stroke-width="1.6"/>')
        icx = x + cw/2
        s += (f'<g transform="translate({icx-ic/2:.1f},{y0:.1f}) scale({ic/100:.4f})">'
              f'{V.icon(it[0])}</g>')
        y = y0 + ic + fst*1.05
        s += tspan(icx, y, tls[i], 'bold', fst, V.OLIVA)
        if sls[i]:
            y += len(tls[i])*fst*1.22 + fss*0.4
            s += tspan(icx, y, sls[i], 'med', fss, V.VERDE)
    return s + '</svg>'


def rotulo(w_in, h_in):
    """Maqueta de un rótulo de evidencia con los tres campos obligatorios."""
    W, H = w_in*UPI, h_in*UPI
    s = V.svg_open(W, H)
    s += (f'<rect x="2" y="2" width="{W-4:.1f}" height="{H-4:.1f}" rx="{H*0.07:.1f}" '
          f'fill="#FFFFFF" stroke="{V.OLIVA}" stroke-width="3"/>')
    hb = H*0.24
    s += (f'<path d="M2 {hb:.1f} V{H*0.07:.1f} a{H*0.07:.1f} {H*0.07:.1f} 0 0 1 {H*0.07:.1f} -{H*0.07:.1f} '
          f'H{W-2-H*0.07:.1f} a{H*0.07:.1f} {H*0.07:.1f} 0 0 1 {H*0.07:.1f} {H*0.07:.1f} V{hb:.1f} Z" fill="{V.OLIVA}"/>')
    fsh = min(17, hb*0.52)
    s += tspan(W/2, hb*0.68, ['RÓTULO DE EVIDENCIA'], 'bold', fsh, '#FFFFFF')
    campos = [('etiqueta','CÓDIGO DE IDENTIFICACIÓN','N.º de caso judicial y n.º de indicio'),
              ('formulario','FECHA, HORA Y LUGAR','Momento y ubicación topográfica exacta'),
              ('escudo_check','RESPONSABLE','Grado, nombre, apellidos y firma')]
    n = len(campos); pad = W*0.025
    cw = (W - pad*(n+1)) / n
    ytop = hb + H*0.09
    ch   = H - ytop - H*0.07
    for i,(ico,tit,sub) in enumerate(campos):
        x = pad + i*(cw+pad)
        s += (f'<rect x="{x:.1f}" y="{ytop:.1f}" width="{cw:.1f}" height="{ch:.1f}" rx="{ch*0.10:.1f}" '
              f'fill="{V.SUAVE}" stroke="{V.ORO}" stroke-width="1.8"/>')
        ic = min(ch*0.44, cw*0.16)
        s += (f'<g transform="translate({x+cw*0.045:.1f},{ytop+ch*0.16:.1f}) scale({ic/100:.4f})">'
              f'{V.icon(ico)}</g>')
        tx = x + cw*0.055 + ic + cw*0.045
        fst = max(9.5, min(13, cw*0.072))
        s += tspan(tx, ytop+ch*0.36, wrap(tit,'bold',fst,cw-(tx-x)-cw*0.05)[:2], 'bold', fst, V.OLIVA, anchor='start')
        fss = fst*0.84
        s += tspan(tx, ytop+ch*0.66, wrap(sub,'med',fss,cw-(tx-x)-cw*0.05)[:3], 'med', fss, V.VERDE, anchor='start')
    return s + '</svg>'

def save(svg, path, w_in, dpi=200):
    return V.render(svg, path, int(w_in*dpi))
