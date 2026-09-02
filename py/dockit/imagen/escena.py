"""Imágenes realistas para las diapositivas, generadas en local con SDXL.

Los diagramas de iconos dicen poco: un candado no explica qué es un oráculo.
Aquí se genera una escena que muestre de qué habla la lámina.

Regla inversa a la del diagrama: **SDXL no escribe texto** —lo que produce son
garabatos con forma de letra—, así que la escena ilustra y los rótulos los pone
la diapositiva. Por eso el prompt negativo excluye texto, logotipos y marcas.

La paleta de la lámina entra en el prompt para que la imagen no desentone.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

INTERPRETE = Path.home() / ".local/share/sdgen/bin/python"
MODELO = "stabilityai/sdxl-turbo"
ANCHO, ALTO = 1024, 576          # 16:9, el formato de la lámina
PASOS = 4                        # sdxl-turbo converge en pocos pasos

PROMPT_NEGATIVO = (
    "text, letters, words, captions, watermark, logo, signature, "
    "ui, interface, chart labels, numbers, blurry, deformed hands, "
    "extra fingers, low quality, jpeg artifacts, oversaturated"
)

# Nombre de color legible por el modelo a partir del tono dominante.
def _nombre_color(hexa: str) -> str:
    h = str(hexa).lstrip("#")
    if len(h) != 6:
        return "muted"
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if g > r and g >= b:
        return "teal and deep green" if b > r else "green"
    if b > r and b > g:
        return "deep blue"
    if r > 180 and g > 140:
        return "warm amber"
    if r > g and r > b:
        return "warm red"
    return "muted grey"


# Del vocabulario de la lámina a la escena que la ilustra. En español, porque
# el contenido llega en español; la escena se describe en inglés para SDXL.
ESCENAS: list[tuple[tuple[str, ...], str]] = [
    (("servidor", "infraestruct", "red", "nodo", "centro de datos"),
     "a modern data center aisle with server racks and fiber optic cables"),
    (("dato", "informacion", "fuente", "feed", "flujo"),
     "abstract flowing streams of light representing data moving between systems"),
    (("precio", "mercado", "financ", "trading", "cotiza", "defi"),
     "a financial trading desk with market screens and glowing price charts"),
    (("segur", "ataque", "riesgo", "vulnerab", "amenaza", "fraude"),
     "a dim security operations room with monitors showing network alerts"),
    (("contrato", "legal", "norma", "regul", "acuerdo"),
     "a signed document on a desk beside a laptop in warm office light"),
    (("descentral", "comunidad", "consenso", "particip", "red distribuida"),
     "a glowing network of interconnected nodes spread across a dark surface"),
    (("central", "intermediar", "control", "autoridad", "jerarq"),
     "a single illuminated tower connected by cables to many smaller units"),
    (("verific", "audit", "comprob", "confian", "valid"),
     "hands examining printed reports with a magnifying glass on a wooden desk"),
    (("tiempo", "latencia", "retardo", "sincron"),
     "long exposure photograph of light trails moving through a corridor"),
    (("investig", "academ", "literatura", "estudio"),
     "an open research paper and notebook on a desk under a reading lamp"),
    (("blockchain", "cadena de bloques", "cripto", "token"),
     "abstract chain of translucent geometric blocks connected by light"),
]

ESCENA_NEUTRA = ("abstract technological background with layered geometric "
                 "shapes and soft depth of field")

ESTILO = ("professional editorial photograph, cinematic lighting, shallow "
          "depth of field, clean composition, negative space on one side, "
          "high detail, 16:9")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s).lower())
    return s.encode("ascii", "ignore").decode()


def _escena_para(texto: str, usadas: set[str] | None = None) -> str:
    """Escena base para este texto, evitando repetir dentro de la misma
    presentación: dos láminas con la misma imagen se notan enseguida."""
    plano = _norm(texto)
    candidatas = [esc for claves, esc in ESCENAS
                  if any(c in plano for c in claves)]
    if usadas is not None:
        libre = next((c for c in candidatas if c not in usadas), None)
        if libre is None:
            libre = next((esc for _, esc in ESCENAS if esc not in usadas),
                         candidatas[0] if candidatas else ESCENA_NEUTRA)
        usadas.add(libre)
        return libre
    return candidatas[0] if candidatas else ESCENA_NEUTRA


# Encuadres alternativos: aunque dos láminas compartan escena base, cambiando
# el punto de vista la imagen deja de parecer la misma.
ENCUADRES = ("wide establishing shot", "close-up detail", "overhead view",
             "low angle perspective", "over-the-shoulder framing")


def prompt_base(titulo: str, vinetas: list[str], paleta: dict | None = None,
                usadas: set[str] | None = None, indice: int = 0) -> str | None:
    """Prompt en inglés para una escena que ilustre esta lámina."""
    limpias = [v.strip() for v in (vinetas or []) if v and v.strip()]
    if not limpias:
        return None
    color = _nombre_color((paleta or {}).get("primary", "#0B6B61"))
    esc = _escena_para(f"{titulo} {' '.join(limpias)}", usadas)
    encuadre = ENCUADRES[indice % len(ENCUADRES)]
    return (f"{esc}, {encuadre}, {color} color palette, {ESTILO}, "
            f"no text anywhere in the image")


def tarea(titulo: str, vinetas: list[str], paleta: dict | None,
          destino: str, indice: int = 0,
          usadas: set[str] | None = None) -> dict | None:
    """Descripción completa de una escena para el lote.

    La semilla sale del título: estable —regenerar da lo mismo— y distinta
    entre láminas, así que dos prompts parecidos no producen la misma imagen.
    """
    prompt = prompt_base(titulo, vinetas, paleta, usadas, indice)
    if prompt is None:
        return None
    # hashlib y no hash(): el hash de Python cambia entre procesos, así que
    # regenerar el trabajo daría imágenes distintas cada vez
    digest = hashlib.sha256(_norm(titulo).encode("utf-8")).digest()
    semilla = int.from_bytes(digest[:4], "big") % 2_000_000_000 or 1
    return {"prompt": prompt, "destino": destino, "semilla": semilla}


def disponible() -> bool:
    """¿Se puede generar aquí y ahora? Sin GPU, no se intenta."""
    if not INTERPRETE.exists():
        return False
    try:
        r = subprocess.run(
            [str(INTERPRETE), "-c",
             "import torch,diffusers;print(int(torch.cuda.is_available()))"],
            capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0 and r.stdout.strip().endswith("1")


GUION_GENERADOR = r'''
import json, sys
from pathlib import Path
import torch
from diffusers import AutoPipelineForText2Image

peticion = json.loads(Path(sys.argv[1]).read_text())
pipe = AutoPipelineForText2Image.from_pretrained(
    peticion["modelo"], torch_dtype=torch.float16, variant="fp16",
    local_files_only=True)
# La 3070 tiene 8 GB: sin descarga por capas se queda sin memoria.
pipe.enable_model_cpu_offload()
pipe.set_progress_bar_config(disable=True)

salidas = []
for tarea in peticion["tareas"]:
    generador = None
    if tarea.get("semilla"):
        generador = torch.Generator(device="cpu").manual_seed(int(tarea["semilla"]))
    imagen = pipe(
        prompt=tarea["prompt"],
        generator=generador,
        negative_prompt=peticion["negativo"],
        num_inference_steps=peticion["pasos"],
        guidance_scale=0.0,          # sdxl-turbo no usa guidance
        width=peticion["ancho"], height=peticion["alto"],
    ).images[0]
    imagen.save(tarea["destino"])
    salidas.append(tarea["destino"])
print(json.dumps(salidas))
'''


def liberar_gpu(modelos: list[str] | None = None) -> None:
    """Descarga de la GPU los modelos de ollama antes de generar imágenes.

    En una tarjeta de 8 GB no caben a la vez un modelo de lenguaje de 7B
    (4,6 GB) y SDXL. Para cuando toca ilustrar, el texto ya está escrito y el
    índice consultado, así que el modelo de lenguaje sobra ahí.
    """
    if not shutil.which("ollama"):
        return
    for modelo in (modelos or []):
        try:
            subprocess.run(["ollama", "stop", modelo],
                           capture_output=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            pass


def generar_lote(tareas: list[dict], pasos: int = PASOS,
                 liberar: list[str] | None = None) -> list[Path]:
    """Genera varias escenas en una sola carga del modelo.

    Cargar SDXL cuesta más que generar: hacerlo una vez por lámina multiplica
    el tiempo por ocho sin ninguna ganancia.
    """
    if not tareas or not disponible():
        return []
    import json
    import tempfile
    import time

    if liberar:
        liberar_gpu(liberar)
        time.sleep(2)      # ollama tarda un instante en soltar la memoria

    with tempfile.TemporaryDirectory() as tmp:
        guion = Path(tmp) / "gen.py"
        guion.write_text(GUION_GENERADOR, encoding="utf-8")
        peticion = Path(tmp) / "peticion.json"
        peticion.write_text(json.dumps({
            "modelo": MODELO, "negativo": PROMPT_NEGATIVO, "pasos": pasos,
            "ancho": ANCHO, "alto": ALTO, "tareas": tareas,
        }), encoding="utf-8")
        try:
            r = subprocess.run([str(INTERPRETE), str(guion), str(peticion)],
                               capture_output=True, text=True, timeout=1800)
        except subprocess.TimeoutExpired:
            print("  aviso: SDXL tardó demasiado; sigo sin escenas")
            return []
    if r.returncode != 0:
        detalle = (r.stderr or "").strip().splitlines()
        print(f"  aviso: SDXL falló ({detalle[-1] if detalle else 'sin detalle'})")
        return []
    try:
        return [Path(p) for p in json.loads(r.stdout.strip().splitlines()[-1])]
    except (json.JSONDecodeError, IndexError):
        return [Path(t["destino"]) for t in tareas
                if Path(t["destino"]).exists()]


def generar(titulo: str, vinetas: list[str], destino_dir: Path, nombre: str,
            paleta: dict | None = None) -> Path | None:
    """Una sola escena. Para varias, usa `generar_lote`."""
    prompt = prompt_base(titulo, vinetas, paleta)
    if prompt is None:
        return None
    destino_dir = Path(destino_dir)
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = destino_dir / f"{nombre}.png"
    salidas = generar_lote([{"prompt": prompt, "destino": str(destino)}])
    return salidas[0] if salidas else None
