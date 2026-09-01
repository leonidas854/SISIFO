#!/usr/bin/env python3
"""Valida cobertura, integridad y similitud de las tres opciones por diapositiva."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("imagenes", type=Path)
    parser.add_argument("--contactos", type=Path)
    parser.add_argument("--informe", type=Path)
    return parser.parse_args()


def target(root: Path, item: dict) -> Path:
    stem = root / f"tema{int(item['tema']):02d}" / (
        f"diapo{int(item['diapositiva']):02d}_op{int(item['opcion'])}"
    )
    for suffix in (".png", ".jpg", ".jpeg", ".webp"):
        candidate = stem.with_suffix(suffix)
        if candidate.exists():
            return candidate
    return stem.with_suffix(".jpg")


def dhash(image: Image.Image, size: int = 12) -> int:
    gray = image.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    pixels = list(gray.getdata())
    value = 0
    for y in range(size):
        row = y * (size + 1)
        for x in range(size):
            value = (value << 1) | (pixels[row + x] > pixels[row + x + 1])
    return value


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def load_plan(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["trabajos"] if isinstance(payload, dict) else payload


def make_contact_sheet(theme: int, rows: dict[int, list[tuple[int, Path]]], out: Path) -> None:
    thumb_w, thumb_h = 384, 216
    label_h, gap = 28, 10
    slides = sorted(rows)
    canvas = Image.new(
        "RGB",
        (3 * thumb_w + 4 * gap, len(slides) * (thumb_h + label_h + gap) + gap),
        "#e8e8e5",
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=18)
    for row, slide in enumerate(slides):
        for column, (option, path) in enumerate(sorted(rows[slide])):
            with Image.open(path) as image:
                tile = image.convert("RGB")
                tile.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                background = Image.new("RGB", (thumb_w, thumb_h), "white")
                x0 = (thumb_w - tile.width) // 2
                y0 = (thumb_h - tile.height) // 2
                background.paste(tile, (x0, y0))
            x = gap + column * (thumb_w + gap)
            y = gap + row * (thumb_h + label_h + gap)
            canvas.paste(background, (x, y))
            draw.text((x + 4, y + thumb_h + 3), f"D{slide:02d} · opción {option}", fill="#1f2b14", font=font)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, "JPEG", quality=90, optimize=True)


def main() -> None:
    args = parse_args()
    jobs = load_plan(args.plan)
    expected = {(int(j["tema"]), int(j["diapositiva"]), int(j["opcion"])) for j in jobs}
    missing: list[str] = []
    corrupt: list[str] = []
    dimensions: dict[str, list[int]] = {}
    exact: dict[str, list[str]] = defaultdict(list)
    perceptual: dict[tuple[int, int], list[tuple[int, int, Path]]] = defaultdict(list)
    sheets: dict[int, dict[int, list[tuple[int, Path]]]] = defaultdict(lambda: defaultdict(list))

    for theme, slide, option in sorted(expected):
        path = target(args.imagenes, {"tema": theme, "diapositiva": slide, "opcion": option})
        if not path.exists():
            missing.append(str(path))
            continue
        try:
            payload = path.read_bytes()
            exact[hashlib.sha256(payload).hexdigest()].append(str(path))
            with Image.open(path) as image:
                image.load()
                dimensions[str(path)] = [image.width, image.height]
                perceptual[(theme, slide)].append((option, dhash(image), path))
            sheets[theme][slide].append((option, path))
        except Exception as exc:
            corrupt.append(f"{path}: {exc!r}")

    exact_duplicates = [paths for paths in exact.values() if len(paths) > 1]
    near_duplicates: list[dict] = []
    for (theme, slide), options in perceptual.items():
        for index, (op_a, hash_a, path_a) in enumerate(options):
            for op_b, hash_b, path_b in options[index + 1 :]:
                distance = hamming(hash_a, hash_b)
                if distance <= 10:
                    near_duplicates.append(
                        {
                            "tema": theme,
                            "diapositiva": slide,
                            "opciones": [op_a, op_b],
                            "distancia_dhash": distance,
                            "archivos": [str(path_a), str(path_b)],
                        }
                    )

    if args.contactos:
        for theme, rows in sheets.items():
            complete_rows = {slide: items for slide, items in rows.items() if len(items) == 3}
            if complete_rows:
                make_contact_sheet(theme, complete_rows, args.contactos / f"tema{theme:02d}.jpg")

    report = {
        "esperadas": len(expected),
        "presentes": len(dimensions),
        "faltantes": missing,
        "corruptas": corrupt,
        "duplicados_exactos": exact_duplicates,
        "posibles_duplicados_visuales": near_duplicates,
        "dimensiones": dimensions,
    }
    destination = args.informe or args.imagenes / "informe_validacion.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: len(value) if isinstance(value, list) else value for key, value in report.items() if key != "dimensiones"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
