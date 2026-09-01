#!/usr/bin/env python3
"""Genera propuestas de objetos y lugares con SDXL-Turbo usando un plan JSON.

El script es reanudable y no sobrescribe imágenes existentes salvo que se use
``--force``. Cada entrada del plan debe tener, como mínimo:

    {
      "tema": 3,
      "diapositiva": 2,
      "opcion": 1,
      "prompt": "...",
      "motor": "sdxl"
    }

Las imágenes se guardan como ``tema03/diapo02_op1.jpg``.
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
PROMPT_SUFFIX = (
    " Bolivia, realistic professional documentary photo, natural light, clean "
    "horizontal 16:9 composition. No police uniforms, insignia, readable text, "
    "logos or watermark. Normal anatomy, hands and faces; no duplicated people."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path, help="Archivo JSON con una lista de trabajos")
    parser.add_argument("salida", type=Path, help="Carpeta raíz de las imágenes")
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=576)
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0, help="0 procesa todo")
    parser.add_argument("--tema", type=int, action="append", dest="temas")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--sin-offload", action="store_true")
    return parser.parse_args()


def stable_seed(entry: dict) -> int:
    key = f"{entry['tema']}:{entry['diapositiva']}:{entry['opcion']}:{entry['prompt']}"
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16)


def output_path(root: Path, entry: dict) -> Path:
    return root / f"tema{int(entry['tema']):02d}" / (
        f"diapo{int(entry['diapositiva']):02d}_op{int(entry['opcion'])}.jpg"
    )


def load_jobs(path: Path, temas: list[int] | None) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    jobs = payload["trabajos"] if isinstance(payload, dict) else payload
    if not isinstance(jobs, list):
        raise ValueError("El plan debe ser una lista o contener la clave 'trabajos'")
    # Los planes expandidos también incluyen los diagramas vectoriales, que no
    # llevan prompt. Se filtran antes de validar el contrato de SDXL.
    jobs = [
        job
        for job in jobs
        if str(job.get("motor", "sdxl")).lower() in {"sdxl", "local", "sdxl-turbo"}
    ]
    required = {"tema", "diapositiva", "opcion"}
    for index, job in enumerate(jobs, 1):
        missing = required - set(job)
        if missing:
            raise ValueError(f"Trabajo {index}: faltan {sorted(missing)}")
        # SDXL sólo admite 77 tokens CLIP. El prompt específico del plan lleva
        # la escena; ``prompt_final`` añade bloques largos pensados para
        # imagegen y truncaba precisamente las restricciones importantes.
        prompt = job.get("prompt") or job.get("prompt_final")
        if not prompt:
            raise ValueError(f"Trabajo {index}: falta prompt o prompt_final")
        job["prompt"] = prompt
        if int(job["opcion"]) not in (1, 2, 3):
            raise ValueError(f"Trabajo {index}: opcion debe ser 1, 2 o 3")
    if temas:
        allowed = set(temas)
        jobs = [job for job in jobs if int(job["tema"]) in allowed]
    return jobs


def main() -> int:
    args = parse_args()
    if args.width % 8 or args.height % 8:
        raise SystemExit("width y height deben ser múltiplos de 8")

    jobs = load_jobs(args.plan, args.temas)
    if args.limit:
        jobs = jobs[: args.limit]
    args.salida.mkdir(parents=True, exist_ok=True)

    try:
        import torch
        from diffusers import AutoPipelineForText2Image
    except ImportError as exc:
        raise SystemExit(
            "Faltan dependencias. Ejecute con ~/.local/share/sdgen/bin/python."
        ) from exc

    if not torch.cuda.is_available():
        raise SystemExit("CUDA no está disponible; no se inicia generación en CPU")

    print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)
    print(f"Modelo: {MODEL_ID} (solo caché local)", flush=True)
    pipe = AutoPipelineForText2Image.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        variant="fp16",
        local_files_only=True,
    )
    if args.sin_offload:
        pipe.to("cuda")
    else:
        pipe.enable_model_cpu_offload()
    # Diffusers 0.40 movió estos métodos del pipeline al VAE. Compatibilidad
    # con ambas APIs para que el lote no dependa de una versión concreta.
    for pipeline_name, vae_name in (
        ("enable_vae_slicing", "enable_slicing"),
        ("enable_vae_tiling", "enable_tiling"),
    ):
        method = getattr(pipe, pipeline_name, None)
        if not callable(method):
            method = getattr(getattr(pipe, "vae", None), vae_name, None)
        if callable(method):
            method()
    pipe.set_progress_bar_config(disable=True)

    log_path = args.salida / "registro_generacion.jsonl"
    total = len(jobs)
    generated = skipped = failed = 0
    start_all = time.monotonic()

    for index, job in enumerate(jobs, 1):
        target = output_path(args.salida, job)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not args.force:
            skipped += 1
            print(f"[{index}/{total}] existe {target}", flush=True)
            continue

        seed = int(job.get("semilla", stable_seed(job)))
        prompt = str(job["prompt"]).strip() + PROMPT_SUFFIX
        begin = time.monotonic()
        record = {
            "tema": int(job["tema"]),
            "diapositiva": int(job["diapositiva"]),
            "opcion": int(job["opcion"]),
            "archivo": str(target),
            "semilla": seed,
            "modelo": MODEL_ID,
            "width": args.width,
            "height": args.height,
            "steps": args.steps,
            "prompt": prompt,
        }
        try:
            generator = torch.Generator(device="cuda").manual_seed(seed)
            image = pipe(
                prompt=prompt,
                num_inference_steps=args.steps,
                guidance_scale=0.0,
                width=args.width,
                height=args.height,
                generator=generator,
            ).images[0].convert("RGB")
            temporary = target.with_name(target.stem + ".tmp.jpg")
            image.save(temporary, "JPEG", quality=94, optimize=True)
            os.replace(temporary, target)
            record["estado"] = "generada"
            generated += 1
        except Exception as exc:  # deja registro y sigue con el lote
            record["estado"] = "error"
            record["error"] = repr(exc)
            failed += 1
        record["segundos"] = round(time.monotonic() - begin, 3)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(
            f"[{index}/{total}] {record['estado']} {target} "
            f"({record['segundos']} s)",
            flush=True,
        )

    elapsed = time.monotonic() - start_all
    print(
        json.dumps(
            {
                "total": total,
                "generadas": generated,
                "existentes": skipped,
                "errores": failed,
                "segundos": round(elapsed, 2),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
