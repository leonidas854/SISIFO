#!/usr/bin/env python3
"""Resumen compacto de un tema a partir del inventario, para trabajar su semántica."""
import re, sys
from pathlib import Path

INV = Path(__file__).resolve().parent.parent / "analisis" / "inventario_original.md"

def digesto(tema: int) -> str:
    txt = INV.read_text(encoding="utf-8")
    ini = txt.index(f"\n## {tema}_ DIAPOSITIVA")
    sig = re.search(r"\n## \d+_ ?DIAPOSITIVA", txt[ini + 5:])
    bloque = txt[ini:ini + 5 + sig.start()] if sig else txt[ini:]
    out = []
    for m in re.finditer(r"### Diapositiva (\d+): (.+?)\n(.*?)(?=\n### |\Z)", bloque, re.S):
        n, titulo, cuerpo = m.group(1), m.group(2).strip().replace("\n", " / "), m.group(3)
        lineas = [l.strip("- ").strip() for l in re.findall(r"^   - (.+)$", cuerpo, re.M)]
        vistos, limpio = set(), []
        for l in lineas:
            if l.lower() != titulo.lower() and l not in vistos:
                vistos.add(l); limpio.append(l)
        out.append(f"[{n}] {titulo}\n" + "\n".join(f"    · {l}" for l in limpio))
    return "\n".join(out)

if __name__ == "__main__":
    for t in sys.argv[1:]:
        print(f"\n{'='*70}\nTEMA {t}\n{'='*70}")
        print(digesto(int(t)))
