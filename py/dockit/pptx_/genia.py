# -*- coding: utf-8 -*-
"""Genera imágenes con SDXL-Turbo en la GPU local.
Reglas fijas del prompt negativo: nada de texto, insignias, banderas ni escudos,
porque la IA los inventa y en un material policial oficial eso es inaceptable."""
import os, sys, json, torch
from diffusers import AutoPipelineForText2Image

MODELO = 'stabilityai/sdxl-turbo'
NEGATIVO = ('text, letters, words, watermark, signature, logo, badge, emblem, insignia, '
            'flag, patch, crest, shield with text, license plate, distorted hands, '
            'extra fingers, deformed face, blurry, lowres, cartoon, anime, nsfw')
SUFIJO = (', documentary photography, natural daylight, realistic, sharp focus, '
          'neutral plain uniform without insignia, professional, clean composition')

_pipe = None
def pipe():
    global _pipe
    if _pipe is None:
        _pipe = AutoPipelineForText2Image.from_pretrained(
            MODELO, torch_dtype=torch.float16, variant='fp16')
        # La 3070 tiene 8 GB y el escritorio ya ocupa parte: se cargan a GPU solo
        # los componentes en uso, y el VAE trabaja por bloques.
        _pipe.enable_model_cpu_offload()
        for m in ('enable_vae_slicing', 'enable_vae_tiling'):
            fn = getattr(_pipe, m, None) or getattr(getattr(_pipe, 'vae', None), m.replace('enable_vae_','enable_'), None)
            if callable(fn):
                fn()
        _pipe.set_progress_bar_config(disable=True)
    return _pipe

def generar(prompt, salida, w=1024, h=640, pasos=4, semilla=None):
    g = torch.Generator('cuda')
    g = g.manual_seed(semilla) if semilla is not None else g
    im = pipe()(prompt=prompt+SUFIJO, negative_prompt=NEGATIVO,
                num_inference_steps=pasos, guidance_scale=0.0,
                width=w, height=h, generator=g).images[0]
    im.save(salida, quality=95)
    return salida

if __name__ == '__main__':
    plan = json.load(open(sys.argv[1]))
    out = sys.argv[2] if len(sys.argv) > 2 else 'ia'
    os.makedirs(out, exist_ok=True)
    for nombre, prompt in plan.items():
        f = f'{out}/{nombre}.jpg'
        if os.path.exists(f):
            print('ya existe', nombre); continue
        generar(prompt, f, semilla=abs(hash(nombre)) % 100000)
        print('generado', nombre)
