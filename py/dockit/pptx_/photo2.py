# -*- coding: utf-8 -*-
"""Prepara la foto para la diapositiva.
Dos modos, elegidos automáticamente según el fondo de la imagen:
  'fundido' -> fondo claro: se difumina hacia el blanco y el objeto queda flotando
               sobre la plantilla, sin marco (así se ve el ejemplo del usuario).
  'recorte' -> fondo oscuro: rectángulo limpio, sin borde duro.
"""
import numpy as np
from PIL import Image, ImageOps, ImageFilter, ImageChops


def recortar_blanco(im, umbral=242, margen=0.012):
    """Quita el marco blanco sobrante para que el objeto llene el cuadro.
    Es lo que hace que la foto se vea grande sin ocupar más sitio."""
    g = im.convert('L')
    mask = g.point(lambda p: 255 if p < umbral else 0)
    caja = mask.getbbox()
    if not caja: return im
    x0, y0, x1, y1 = caja
    if (x1-x0) < im.width*0.35 or (y1-y0) < im.height*0.35:
        return im                                  # recorte sospechoso: mejor no tocar
    mx, my = int(im.width*margen), int(im.height*margen)
    return im.crop((max(0,x0-mx), max(0,y0-my),
                    min(im.width,x1+mx), min(im.height,y1+my)))


DPI = 200

def borde_claro(im, umbral=198):
    a = np.asarray(im.convert('RGB').resize((150,150))).astype(float).mean(axis=2)
    b = np.concatenate([a[:8].ravel(), a[-8:].ravel(), a[:,:8].ravel(), a[:,-8:].ravel()])
    return float(b.mean()) >= umbral, float(b.mean())

def _mascara_fundido(W, H, margen=0.035):
    """Alfa que vale 1 en el centro y baja a 0 en los bordes."""
    mx, my = max(2, int(W*margen)), max(2, int(H*margen))
    m = Image.new('L', (W, H), 0)
    m.paste(255, (mx, my, W-mx, H-my))
    return m.filter(ImageFilter.GaussianBlur(radius=max(2, min(mx, my)*0.8)))

def preparar(src, out, w_in, h_in, modo='auto', centro=(0.5,0.45)):
    W, H = int(w_in*DPI), int(h_in*DPI)
    im = Image.open(src).convert('RGB')
    if modo == 'auto':
        claro, _ = borde_claro(im)
        modo = 'fundido' if claro else 'recorte'
    if modo == 'fundido':
        im = recortar_blanco(im)
    im = ImageOps.fit(im, (W, H), method=Image.LANCZOS, centering=centro)
    if modo == 'fundido':
        fondo = Image.new('RGB', (W, H), (255,255,255))
        fondo.paste(im, (0,0), _mascara_fundido(W, H))
        im = fondo
    im.save(out, quality=95)
    return out, modo

def encuadre(free, im_path, margen=0.08, align='left', valign='top', amin=1.0, amax=2.6,
             expandir=1.0, slide_w=13.33, slide_h=7.5):
    """Mayor rectángulo aprovechable dentro del hueco, con la proporción natural de la foto.
    `expandir` deja que las imágenes de fondo claro se pasen un poco del hueco: como sus
    bordes se funden en blanco, no chocan visualmente con el texto."""
    L, T, W, H = free['left'], free['top'], free['w'], free['h']
    iw, ih = W - 2*margen, H - 2*margen
    with Image.open(im_path) as t:
        t = t.convert('RGB')
        claro, _ = borde_claro(t)
        if claro: t = recortar_blanco(t)
        nat = t.width / t.height
    a = max(amin, min(amax, nat))
    if iw/ih > a: iw = ih*a
    else:         ih = iw/a
    iw, ih = iw*expandir, ih*expandir
    cx = (L + margen + 0.16 + iw/2) if align == 'left' else \
         (L + W - margen - iw/2)    if align == 'right' else (L + W/2)
    if valign == 'top':
        y = T + margen
    elif valign == 'bottom':
        y = T + H - margen - ih
    else:
        y = T + (H - ih)/2
    x = cx - iw/2
    x = max(0.12, min(x, slide_w - iw - 0.12))
    y = max(0.12, min(y, slide_h - ih - 0.22))
    return round(x,2), round(y,2), round(iw,2), round(ih,2)


def es_afiche(src):
    """Descarta láminas de texto, afiches e infografías: son diapositivas ajenas.
    Se reconocen por dos rasgos: muchas filas con densidad de borde propia de
    renglones de texto, o una paleta muy plana con bordes duros de recuadro."""
    try:
        im = Image.open(src).convert('RGB')
    except Exception:
        return False
    ch = im.resize((260, 260))
    g  = np.asarray(ch.convert('L')).astype(float)
    hb = np.abs(np.diff(g, axis=1)) > 42
    filas_texto = float((hb.mean(axis=1) > 0.18).mean())
    densidad    = float(hb.mean())
    colores     = len(ch.getcolors(maxcolors=1 << 20) or [])
    if filas_texto > 0.14:                     # renglones de texto
        return True
    return colores < 9000 and densidad > 0.045  # paleta plana con recuadros
