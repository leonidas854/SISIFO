#!/usr/bin/env python3
"""Combina y valida planes parciales de tres opciones por diapositiva."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


CONTENT_RANGES = {
    3: range(2, 18),
    4: range(2, 18),
    5: range(2, 18),
    6: range(2, 23),
    7: range(2, 20),
    8: range(2, 21),
    9: range(2, 16),
    10: range(2, 17),
    11: range(2, 20),
    12: range(2, 19),
    13: range(2, 25),
    14: range(2, 23),
}
LOCAL_MOTORS = {"sdxl", "local", "sdxl-turbo"}
IMAGEGEN_MOTORS = {"imagegen", "image_gen"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("planes", nargs="+", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--piloto", type=Path)
    return parser.parse_args()


def read_jobs(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    jobs = payload.get("trabajos", payload) if isinstance(payload, dict) else payload
    if not isinstance(jobs, list):
        raise ValueError(f"{path}: no contiene una lista de trabajos")
    return jobs


def read_pilot(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    jobs = []
    for option in payload["opciones"]:
        jobs.append(
            {
                "tema": int(payload["tema"]),
                "diapositiva": int(payload["diapositiva"]),
                "opcion": int(option["opcion"]),
                "titulo": payload["titulo"],
                "concepto_visual": option["concepto_visual"],
                "motor": payload.get("motor", "imagegen"),
                "referencias": option.get("referencias", []),
                "prompt": option["prompt"],
                "post_edicion": option.get("post_edicion"),
                "archivo": option.get("archivo"),
                "estado": payload.get("estado"),
            }
        )
    return jobs


def expected_keys() -> set[tuple[int, int, int]]:
    return {
        (theme, slide, option)
        for theme, slides in CONTENT_RANGES.items()
        for slide in slides
        for option in (1, 2, 3)
    }


def main() -> None:
    args = parse_args()
    jobs: list[dict] = []
    for path in args.planes:
        jobs.extend(read_jobs(path))

    if args.piloto:
        pilot_jobs = read_pilot(args.piloto)
        pilot_keys = {
            (int(job["tema"]), int(job["diapositiva"]), int(job["opcion"]))
            for job in pilot_jobs
        }
        jobs = [
            job
            for job in jobs
            if (int(job["tema"]), int(job["diapositiva"]), int(job["opcion"]))
            not in pilot_keys
        ]
        jobs.extend(pilot_jobs)

    required = {
        "tema",
        "diapositiva",
        "opcion",
        "titulo",
        "concepto_visual",
        "motor",
        "referencias",
        "prompt",
    }
    seen: dict[tuple[int, int, int], Path | None] = {}
    errors: list[str] = []
    motor_counts: Counter[str] = Counter()
    theme_counts: Counter[int] = Counter()
    concepts: dict[tuple[int, int], list[str]] = defaultdict(list)

    for index, job in enumerate(jobs, 1):
        missing_fields = required - set(job)
        if missing_fields:
            errors.append(f"trabajo {index}: faltan campos {sorted(missing_fields)}")
            continue
        key = (int(job["tema"]), int(job["diapositiva"]), int(job["opcion"]))
        if key in seen:
            errors.append(f"clave duplicada {key}")
        seen[key] = None
        motor = str(job["motor"]).lower()
        if motor not in LOCAL_MOTORS | IMAGEGEN_MOTORS:
            errors.append(f"{key}: motor no válido {motor!r}")
        if int(job["opcion"]) not in (1, 2, 3):
            errors.append(f"{key}: opción fuera de 1..3")
        if len(str(job["prompt"]).strip()) < 140:
            errors.append(f"{key}: prompt demasiado corto")
        refs = job.get("referencias")
        if not isinstance(refs, list):
            errors.append(f"{key}: referencias no es lista")
        elif motor in IMAGEGEN_MOTORS:
            for reference in refs:
                reference_path = Path(reference)
                if not reference_path.is_absolute():
                    reference_path = args.workspace / reference_path
                if not reference_path.exists():
                    errors.append(f"{key}: referencia inexistente {reference}")
        motor_counts[motor] += 1
        theme_counts[key[0]] += 1
        concepts[(key[0], key[1])].append(str(job["concepto_visual"]).strip().casefold())

    for slide_key, values in concepts.items():
        if len(values) == 3 and len(set(values)) < 3:
            errors.append(f"{slide_key}: conceptos visuales repetidos")

    expected = expected_keys()
    actual = set(seen)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"faltan {len(missing)} claves; primeras: {missing[:12]}")
    if extra:
        errors.append(f"sobran {len(extra)} claves; primeras: {extra[:12]}")

    if errors:
        raise SystemExit("\n".join(f"ERROR: {error}" for error in errors))

    jobs.sort(key=lambda job: (int(job["tema"]), int(job["diapositiva"]), int(job["opcion"])))
    output = {
        "version": 1,
        "descripcion": "Tres alternativas por cada diapositiva de contenido; portadas y GRACIAS excluidas.",
        "resumen": {
            "diapositivas": len(expected) // 3,
            "trabajos": len(jobs),
            "por_motor": dict(sorted(motor_counts.items())),
            "por_tema": {str(key): value for key, value in sorted(theme_counts.items())},
        },
        "trabajos": jobs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output["resumen"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
