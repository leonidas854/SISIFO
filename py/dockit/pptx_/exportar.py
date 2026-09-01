# -*- coding: utf-8 -*-
"""Exporta, por tema, las imágenes usadas y hasta 2 alternativas por diapositiva,
para poder cambiarlas a mano en OnlyOffice."""
import json, os, glob, shutil
from PIL import Image
import photo2 as P2

def alternativas(f, webdir='web2', n=3):
    tag = f['q'].replace(' ','_')[:44]
    return sorted(glob.glob(f'{webdir}/{tag}_*.jpg'))[:n]

def exportar(tema, plan, outdir):
    os.makedirs(outdir, exist_ok=True)
    filas = plan[tema]
    idx = []
    for f in filas:
        n = f['n']
        usada = glob.glob(f'salida/imagenes_tema{tema}/diapo{n:02d}.*')
        if usada:
            ext = os.path.splitext(usada[0])[1]
            shutil.copy(usada[0], f'{outdir}/diapo{n:02d}_usada{ext}')
        ops = alternativas(f) if f['tipo'] in ('foto','ia') else []
        k = 0
        for o in ops:
            if usada and os.path.basename(o) == os.path.basename(usada[0]): continue
            k += 1
            if k > 2: break
            try:
                im = Image.open(o).convert('RGB')
                claro, _ = P2.borde_claro(im)
                if claro: im = P2.recortar_blanco(im)
                im.thumbnail((1600,1600))
                im.save(f'{outdir}/diapo{n:02d}_op{k}.jpg', quality=93)
            except Exception:
                pass
        idx.append(dict(diapo=n, titulo=f['titulo'], tipo=f['tipo'], consulta=f['q']))
    json.dump(idx, open(f'{outdir}/indice.json','w'), ensure_ascii=False, indent=1)
    return len(idx)

if __name__ == '__main__':
    import sys
    plan = json.load(open('plan_full.json'))
    for t in sys.argv[1:]:
        d = f'salida/sueltas_tema{t}'
        print(f'TEMA {t}: {exportar(t, plan, d)} diapositivas -> {d}')
