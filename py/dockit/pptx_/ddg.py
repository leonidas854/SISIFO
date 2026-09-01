# -*- coding: utf-8 -*-
"""Busca imágenes en la web (DuckDuckGo) con consultas en español y filtra por calidad.
Puntúa mejor las que tienen fondo claro, porque se funden con la plantilla como en el
ejemplo que trajo el usuario."""
import requests, re, os, io, json, hashlib, time
import numpy as np
from PIL import Image

UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126 Safari/537.36')
S = requests.Session(); S.headers.update({'User-Agent': UA})
_vqd = {}

def vqd(q):
    if q not in _vqd:
        r = S.get('https://duckduckgo.com/', params={'q': q}, timeout=25)
        m = re.search(r'vqd=["\']?([\d-]+)', r.text)
        _vqd[q] = m.group(1) if m else None
        time.sleep(0.6)
    return _vqd[q]

def buscar(q, n=40):
    v = vqd(q)
    if not v: return []
    r = S.get('https://duckduckgo.com/i.js',
              params={'l':'es-es','o':'json','q':q,'vqd':v,'f':'','p':'1'},
              headers={'Referer':'https://duckduckgo.com/'}, timeout=25)
    if not r.ok: return []
    return r.json().get('results', [])[:n]

def calidad(im):
    """Devuelve (claridad_del_borde, contraste, nitidez_aprox)."""
    a = np.asarray(im.convert('RGB').resize((160,160))).astype(float)
    g = a.mean(axis=2)
    borde = np.concatenate([g[:6].ravel(), g[-6:].ravel(), g[:,:6].ravel(), g[:,-6:].ravel()])
    nitidez = float(np.abs(np.diff(g, axis=0)).mean() + np.abs(np.diff(g, axis=1)).mean())
    return float(borde.mean()), float(g.std()), nitidez

def puntuar(im, orden):
    claro, contraste, nitidez = calidad(im)
    w, h = im.size
    p  = 0.0
    p += min(claro, 245) / 245 * 34          # fondo claro: se funde con la diapositiva
    p += min(contraste, 70) / 70 * 22        # con contraste, no lavada
    p += min(nitidez, 12) / 12 * 18          # con detalle
    p += min(w*h, 1.6e6) / 1.6e6 * 16        # resolución
    p += max(0, 10 - orden*0.35)             # relevancia según el buscador
    return p

def descargar(url, dest):
    try:
        b = S.get(url, timeout=25).content
        im = Image.open(io.BytesIO(b))
        im.load()
        return im.convert('RGB')
    except Exception:
        return None

def recolectar(tag, queries, outdir='web', por_tag=8, min_lado=620):
    os.makedirs(outdir, exist_ok=True)
    vistos, cands = set(), []
    for q in queries:
        for i, it in enumerate(buscar(q)):
            u = it.get('image')
            if not u or u in vistos: continue
            vistos.add(u)
            if it.get('width',0) < min_lado or it.get('height',0) < 420: continue
            ar = it['width']/it['height']
            if not (0.85 < ar < 2.6): continue
            im = descargar(u, None)
            if im is None or im.width < min_lado: continue
            cands.append((puntuar(im, i), im, it, q))
            if len(cands) >= por_tag*4: break
        if len(cands) >= por_tag*4: break
    cands.sort(key=lambda x: -x[0])
    salida = []
    for k, (p, im, it, q) in enumerate(cands[:por_tag]):
        im.thumbnail((1700,1700))
        f = f'{outdir}/{tag}_{k:02d}.jpg'
        im.save(f, quality=93)
        salida.append(dict(file=f, punt=round(p,1), title=it.get('title','')[:80],
                           src=it.get('url',''), q=q, w=im.width, h=im.height))
    return salida

if __name__ == '__main__':
    import sys
    plan = json.load(open(sys.argv[1]))
    out  = {}
    for tag, qs in plan.items():
        r = recolectar(tag, qs)
        out[tag] = r
        print(f'== {tag}: {len(r)}')
        for x in r: print(f'   {x["punt"]:5.1f}  {x["w"]}x{x["h"]}  {x["title"][:52]}')
    json.dump(out, open('web/meta.json','w'), ensure_ascii=False, indent=1)
