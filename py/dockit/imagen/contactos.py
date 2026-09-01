#!/usr/bin/env python3
"""Hoja de contacto de los diagramas de un tema, para revisarlos de un vistazo."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

def hoja(tema: int, cols: int = 5, cw: int = 380, ch: int = 285) -> Path:
    ps = sorted(Path(f"imagenes/tema{tema:02d}").glob("diapo*_op1.png"))
    filas = max(1, (len(ps) + cols - 1) // cols)
    img = Image.new("RGB", (cols * cw, filas * ch), "white")
    d = ImageDraw.Draw(img)
    for i, p in enumerate(ps):
        x, y = (i % cols) * cw, (i // cols) * ch
        im = Image.open(p).convert("RGB")
        im.thumbnail((cw - 8, ch - 26))
        img.paste(im, (x + (cw - im.width) // 2, y + 20))
        d.text((x + 8, y + 5), p.stem.replace("_op1", ""), fill="#455119")
        d.rectangle([x, y, x + cw - 1, y + ch - 1], outline="#D8D5C8")
    out = Path("indices") / f"tema{tema:02d}_diagramas.jpg"
    out.parent.mkdir(exist_ok=True)
    img.save(out, quality=86)
    return out

if __name__ == "__main__":
    for t in (sys.argv[1:] or range(3, 15)):
        print(hoja(int(t)))
