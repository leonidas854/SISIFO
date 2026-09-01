#!/usr/bin/env python3
"""Entrada de terminal al caso de uso visual de SISIFO.

    sisifo visual plan
    sisifo visual validar
    sisifo visual generar
    sisifo visual auditar --pptx salida/exposicion.pptx

Los subcomandos comparten el mismo dominio que podrá consumir la TUI. La CLI
solo traduce argumentos, imprime el informe y decide el código de salida.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

# Permite ejecutar este archivo directamente desde el puente Go.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from dockit.visual.dominio import (  # type: ignore
        Hallazgo, construir_plan_desde_guion, cargar_plan, validar_plan,
    )
    from dockit.visual.pptx_adapter import auditar_presentacion  # type: ignore
    from dockit.visual.semantica import (  # type: ignore
        SemanticaLexica, SemanticaOllama, puntuar_plan,
    )
    from dockit.visual.vector import generar_plan  # type: ignore
else:
    from .dominio import Hallazgo, construir_plan_desde_guion, cargar_plan, validar_plan
    from .pptx_adapter import auditar_presentacion
    from .semantica import SemanticaLexica, SemanticaOllama, puntuar_plan
    from .vector import generar_plan


def _resolver(carpeta: Path, ruta: str | Path) -> Path:
    ruta = Path(ruta)
    return ruta if ruta.is_absolute() else carpeta / ruta


def _agregar_carpeta(p: argparse.ArgumentParser) -> None:
    p.add_argument("--carpeta", type=Path, default=Path.cwd())


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sisifo visual",
        description="Contrato semántico, SVG informativo y QA de presentaciones",
    )
    sub = p.add_subparsers(dest="orden", required=True)

    plan = sub.add_parser("plan", help="crea plan_visual.json desde guion.json")
    _agregar_carpeta(plan)
    plan.add_argument("--guion", default="guion.json")
    plan.add_argument("--salida", default="plan_visual.json")
    plan.add_argument("--sobrescribir", action="store_true")

    validar = sub.add_parser("validar", help="valida semántica, texto y procedencia")
    _agregar_carpeta(validar)
    validar.add_argument("--plan", default="plan_visual.json")
    validar.add_argument(
        "--semantica", choices=("auto", "ollama", "lexica", "ninguno"), default="auto",
    )
    validar.add_argument("--umbral", type=float, default=0.48)
    validar.add_argument("--json", action="store_true")
    validar.add_argument("--estricto", action="store_true", help="los avisos también fallan")

    generar = sub.add_parser("generar", help="genera SVG con rótulos y fuentes reales")
    _agregar_carpeta(generar)
    generar.add_argument("--plan", default="plan_visual.json")
    generar.add_argument("--destino", default="salida/visuales")
    generar.add_argument("--paleta", choices=("tinta", "institucional"), default="tinta")
    generar.add_argument("--sobrescribir", action="store_true")
    generar.add_argument(
        "--permitir-invalido", action="store_true",
        help="solo para previsualización; nunca para una entrega",
    )

    auditar = sub.add_parser("auditar", help="contrasta un PPTX real con el plan")
    _agregar_carpeta(auditar)
    auditar.add_argument("--pptx", action="append", default=[])
    auditar.add_argument("--plan", default="plan_visual.json")
    auditar.add_argument(
        "--semantica", choices=("ollama", "lexica"), default="lexica",
        help="comparación de propósito y texto alternativo",
    )
    auditar.add_argument("--json", action="store_true")
    auditar.add_argument("--estricto", action="store_true")

    migrar = sub.add_parser("migrar", help="convierte un plan policial legado al contrato v1")
    _agregar_carpeta(migrar)
    migrar.add_argument("--plan", required=True)
    migrar.add_argument("--salida", default="plan_visual.json")
    migrar.add_argument("--sobrescribir", action="store_true")
    return p


def _contar(hallazgos: Iterable[Hallazgo]) -> dict[str, int]:
    conteo = {"error": 0, "aviso": 0, "info": 0}
    for h in hallazgos:
        conteo[h.severidad] = conteo.get(h.severidad, 0) + 1
    return conteo


def _imprimir(hallazgos: list[Hallazgo], *, json_: bool, meta: dict | None = None) -> None:
    conteo = _contar(hallazgos)
    if json_:
        print(json.dumps(
            {"resumen": conteo, "meta": meta or {},
             "hallazgos": [h.como_dict() for h in hallazgos]},
            ensure_ascii=False, indent=2,
        ))
        return
    for h in hallazgos:
        lugar = ""
        if h.diapositiva is not None:
            lugar = f" D{h.diapositiva:02d}"
            if h.opcion is not None:
                lugar += f"/op{h.opcion}"
        marca = {"error": "FALLA", "aviso": "AVISO", "info": " ok "}.get(h.severidad, " ? ")
        print(f"[{marca}]{lugar} {h.codigo}: {h.mensaje}")
        print(f"              ↳ {h.accion}")
    if not hallazgos:
        print("[ ok ] contrato visual sin hallazgos")
    print(f"\n{conteo['error']} error(es), {conteo['aviso']} aviso(s)")
    if meta:
        for clave, valor in meta.items():
            print(f"{clave}: {valor}")


def _codigo(hallazgos: Iterable[Hallazgo], estricto: bool = False) -> int:
    for h in hallazgos:
        if h.severidad == "error" or (estricto and h.severidad == "aviso"):
            return 1
    return 0


def _puntuar(plan, modo: str):
    if modo == "lexica":
        # ``puntuar_plan`` usa léxica cuando el modo no solicita Ollama.
        return puntuar_plan(plan, "lexica")
    return puntuar_plan(plan, modo)


def orden_plan(args: argparse.Namespace) -> int:
    carpeta = args.carpeta.resolve()
    guion_ruta = _resolver(carpeta, args.guion)
    salida = _resolver(carpeta, args.salida)
    if salida.exists() and not args.sobrescribir:
        print(f"{salida} ya existe; usa --sobrescribir", file=sys.stderr)
        return 2
    try:
        guion = json.loads(guion_ruta.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"no existe {guion_ruta}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"{guion_ruta} no es JSON válido: {exc}", file=sys.stderr)
        return 2
    salida.parent.mkdir(parents=True, exist_ok=True)
    borrador = construir_plan_desde_guion(guion)
    salida.write_text(json.dumps(borrador, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"creado {salida}")
    print("completa los TODO, conceptos, texto alternativo y procedencia; luego: sisifo visual validar")
    return 0


def orden_validar(args: argparse.Namespace) -> int:
    ruta = _resolver(args.carpeta.resolve(), args.plan)
    try:
        plan = cargar_plan(ruta)
        puntos, proveedor, aviso = _puntuar(plan, args.semantica)
    except (FileNotFoundError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"no pude validar {ruta}: {exc}", file=sys.stderr)
        return 2
    hallazgos = validar_plan(plan, puntos, umbral_semantico=args.umbral)
    if aviso:
        hallazgos.insert(0, Hallazgo(
            "VIS-051", "aviso", aviso,
            "inicia Ollama con bge-m3 para validar sinónimos y prompts multilingües",
        ))
    _imprimir(hallazgos, json_=args.json, meta={"semántica": proveedor, "plan": str(ruta)})
    return _codigo(hallazgos, args.estricto)


def orden_generar(args: argparse.Namespace) -> int:
    carpeta = args.carpeta.resolve()
    ruta = _resolver(carpeta, args.plan)
    try:
        plan = cargar_plan(ruta)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"no pude leer {ruta}: {exc}", file=sys.stderr)
        return 2
    hallazgos = validar_plan(plan)
    if _codigo(hallazgos) and not args.permitir_invalido:
        _imprimir(hallazgos, json_=False)
        print("\nNo se generó: corrige el contrato o usa --permitir-invalido solo para una previsualización.")
        return 1
    try:
        creados = generar_plan(
            plan, _resolver(carpeta, args.destino), paleta=args.paleta,
            sobrescribir=args.sobrescribir,
        )
    except FileExistsError as exc:
        print(exc, file=sys.stderr)
        return 2
    for ruta_creada in creados:
        print(f"[ ok ] {ruta_creada}")
    print(f"\n{len(creados)} SVG informativos generados; títulos y rótulos siguen siendo texto vectorial.")
    return 0


def _pptx_del_brief(carpeta: Path) -> list[Path]:
    brief = carpeta / "BRIEF.md"
    rutas: list[Path] = []
    if brief.exists():
        try:
            import re
            import yaml

            texto = brief.read_text(encoding="utf-8")
            m = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
            datos = yaml.safe_load(m.group(1)) or {} if m else {}
            for ent in datos.get("entregables") or []:
                archivo = ent.get("archivo")
                tipo = str(ent.get("tipo") or Path(archivo or "").suffix.lstrip(".")).lower()
                if archivo and tipo == "pptx":
                    rutas.append(_resolver(carpeta, archivo))
        except Exception:
            pass
    if not rutas:
        rutas = sorted((carpeta / "salida").glob("*.pptx"))
    return rutas


def orden_auditar(args: argparse.Namespace) -> int:
    carpeta = args.carpeta.resolve()
    plan_ruta = _resolver(carpeta, args.plan)
    plan = cargar_plan(plan_ruta) if plan_ruta.exists() else None
    rutas = [_resolver(carpeta, r) for r in args.pptx] or _pptx_del_brief(carpeta)
    if not rutas:
        print("no encontré un PPTX; usa --pptx ruta o decláralo en BRIEF.md", file=sys.stderr)
        return 2
    proveedor = SemanticaOllama() if args.semantica == "ollama" else SemanticaLexica()
    todos: list[Hallazgo] = []
    for ruta in rutas:
        if not ruta.exists():
            todos.append(Hallazgo(
                "PPT-000", "error", "el PPTX declarado no existe",
                "genera el entregable o corrige su ruta en BRIEF.md", archivo=str(ruta),
            ))
            continue
        try:
            todos.extend(auditar_presentacion(ruta, plan, semantica=proveedor))
        except RuntimeError as exc:
            print(f"falló el proveedor semántico: {exc}", file=sys.stderr)
            return 2
    _imprimir(
        todos, json_=args.json,
        meta={"archivos": len(rutas), "plan": str(plan_ruta) if plan else "sin plan",
              "semántica": proveedor.nombre},
    )
    return _codigo(todos, args.estricto)


def _plan_canonico(plan) -> dict:
    visuales = []
    for v in plan.visuales:
        visuales.append({
            "diapositiva": v.diapositiva,
            "opcion": v.opcion,
            "titulo": v.titulo,
            "proposito": v.proposito,
            "tipo": v.tipo,
            "motor": v.motor,
            "concepto_visual": v.concepto_visual,
            "conceptos": list(v.conceptos),
            "texto_visible": list(v.texto_visible),
            "texto_alternativo": v.texto_alternativo,
            "prompt": v.prompt,
            "procedencia": asdict(v.procedencia),
            "datos": v.datos,
        })
    return {"version": 1, "titulo": plan.titulo, "visuales": visuales}


def orden_migrar(args: argparse.Namespace) -> int:
    carpeta = args.carpeta.resolve()
    origen, salida = _resolver(carpeta, args.plan), _resolver(carpeta, args.salida)
    if salida.exists() and not args.sobrescribir:
        print(f"{salida} ya existe; usa --sobrescribir", file=sys.stderr)
        return 2
    try:
        plan = cargar_plan(origen)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"no pude leer {origen}: {exc}", file=sys.stderr)
        return 2
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(
        json.dumps(_plan_canonico(plan), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"migrado {origen} -> {salida}")
    print("la migración no inventa texto alternativo, procedencia ni etiquetas: validar mostrará lo pendiente")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return {
        "plan": orden_plan,
        "validar": orden_validar,
        "generar": orden_generar,
        "auditar": orden_auditar,
        "migrar": orden_migrar,
    }[args.orden](args)


if __name__ == "__main__":
    raise SystemExit(main())
