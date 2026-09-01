#!/usr/bin/env python3
"""Genera paneles fotográficos sin uniforme con SDXL-Turbo local.

Lee uno o varios ``paneles/planes/temaNN_paneles.json``. Es reanudable,
determinista y limita el prompt a la ventana real de los dos codificadores
CLIP, para que las restricciones importantes nunca queden truncadas.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path


MODEL_ID = "stabilityai/sdxl-turbo"
PREFIX = (
    "Realistic professional documentary photograph in Bolivia. "
    "No readable text, logo, badge, insignia, licence plate or watermark. "
)
SUFFIX = " Natural light, authentic materials, correct anatomy, no duplicated people."


def argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("planes", type=Path, nargs="+", help="JSON de uno o más temas")
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--tema", type=int, action="append", dest="temas")
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--sin-offload", action="store_true")
    return parser.parse_args()


def cargar(planes: list[Path], temas: list[int] | None) -> list[dict]:
    trabajos: list[dict] = []
    permitidos = set(temas or [])
    for archivo in planes:
        data = json.loads(archivo.read_text(encoding="utf-8"))
        for panel in data.get("paneles", []):
            panel = dict(panel)
            panel.setdefault("tema", data.get("tema"))
            if permitidos and int(panel["tema"]) not in permitidos:
                continue
            if str(panel.get("motor", "")).lower() not in {"sdxl", "local", "sdxl-turbo"}:
                continue
            faltan = {"id", "tema", "diapositiva", "rotulo", "prompt"} - set(panel)
            if faltan:
                raise ValueError(f"{archivo}: panel incompleto, faltan {sorted(faltan)}")
            trabajos.append(panel)
    return trabajos


def ruta_salida(raiz: Path, panel: dict) -> Path:
    return raiz / f"tema{int(panel['tema']):02d}" / f"{panel['id']}.jpg"


def semilla(panel: dict) -> int:
    fuente = f"{panel['id']}|{panel['rotulo']}|{panel['prompt']}"
    return int(hashlib.sha256(fuente.encode("utf-8")).hexdigest()[:8], 16)


def cabe(tokenizer, texto: str, limite: int = 77) -> bool:
    return len(
        tokenizer.encode(
            texto, truncation=False, add_special_tokens=True, verbose=False
        )
    ) <= limite


def compactar(prompt_escena: str, tokenizers: list, limite: int = 77) -> str:
    """Conserva el prefijo de seguridad y recorta sólo el final de la escena."""
    escena = " ".join(str(prompt_escena).split())
    palabras = escena.split()
    while palabras:
        candidato = PREFIX + " ".join(palabras) + SUFFIX
        if all(cabe(tok, candidato, limite) for tok in tokenizers):
            return candidato
        palabras.pop()
    minimo = PREFIX + "Plain Bolivian public setting." + SUFFIX
    if not all(cabe(tok, minimo, limite) for tok in tokenizers):
        raise RuntimeError("El prefijo global excede la ventana CLIP")
    return minimo


def main() -> int:
    args = argumentos()
    if args.width % 8 or args.height % 8:
        raise SystemExit("width y height deben ser múltiplos de 8")
    trabajos = cargar(args.planes, args.temas)
    if args.limit:
        trabajos = trabajos[: args.limit]
    args.salida.mkdir(parents=True, exist_ok=True)

    try:
        import torch
        from diffusers import AutoPipelineForText2Image
    except ImportError as exc:
        raise SystemExit("Ejecute con ~/.local/share/sdgen/bin/python") from exc
    if not torch.cuda.is_available():
        raise SystemExit("CUDA no está disponible")

    print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)
    print(f"Modelo: {MODEL_ID} (caché local)", flush=True)
    pipe = AutoPipelineForText2Image.from_pretrained(
        MODEL_ID, torch_dtype=torch.float16, variant="fp16", local_files_only=True
    )
    if args.sin_offload:
        pipe.to("cuda")
    else:
        pipe.enable_model_cpu_offload()
    for pipeline_name, vae_name in (
        ("enable_vae_slicing", "enable_slicing"),
        ("enable_vae_tiling", "enable_tiling"),
    ):
        funcion = getattr(pipe, pipeline_name, None)
        if not callable(funcion):
            funcion = getattr(getattr(pipe, "vae", None), vae_name, None)
        if callable(funcion):
            funcion()
    pipe.set_progress_bar_config(disable=True)
    tokenizers = [pipe.tokenizer]
    if getattr(pipe, "tokenizer_2", None) is not None:
        tokenizers.append(pipe.tokenizer_2)

    registro = args.salida / "registro_sdxl.jsonl"
    hechos = omitidos = errores = 0
    inicio_total = time.monotonic()
    for indice, panel in enumerate(trabajos, 1):
        destino = ruta_salida(args.salida, panel)
        destino.parent.mkdir(parents=True, exist_ok=True)
        if destino.exists() and not args.force:
            omitidos += 1
            print(f"[{indice}/{len(trabajos)}] existe {destino}", flush=True)
            continue
        prompt = compactar(panel["prompt"], tokenizers)
        seed = int(panel.get("semilla", semilla(panel)))
        inicio = time.monotonic()
        fila = {
            "id": panel["id"], "tema": int(panel["tema"]),
            "diapositiva": int(panel["diapositiva"]), "rotulo": panel["rotulo"],
            "archivo": str(destino), "modelo": MODEL_ID, "semilla": seed,
            "prompt": prompt, "width": args.width, "height": args.height,
        }
        try:
            generador = torch.Generator(device="cuda").manual_seed(seed)
            imagen = pipe(
                prompt=prompt, num_inference_steps=args.steps, guidance_scale=0.0,
                width=args.width, height=args.height, generator=generador,
            ).images[0].convert("RGB")
            temporal = destino.with_name(destino.stem + ".tmp.jpg")
            imagen.save(temporal, "JPEG", quality=94, optimize=True)
            os.replace(temporal, destino)
            fila["estado"] = "generada"
            hechos += 1
        except Exception as exc:
            fila.update(estado="error", error=repr(exc))
            errores += 1
        fila["segundos"] = round(time.monotonic() - inicio, 3)
        with registro.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(fila, ensure_ascii=False) + "\n")
        print(f"[{indice}/{len(trabajos)}] {fila['estado']} {destino} ({fila['segundos']} s)", flush=True)

    print(json.dumps({
        "total": len(trabajos), "generadas": hechos, "existentes": omitidos,
        "errores": errores, "segundos": round(time.monotonic() - inicio_total, 2),
    }, ensure_ascii=False), flush=True)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
