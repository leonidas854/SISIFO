"""El repo no puede depender de que exista ninguna carpeta de trabajo.

Si un script del motor apunta con ruta absoluta a `tareas/matmil`, borrar ese
proyecto rompe el motor: exactamente lo que centralizar el código pretendía
evitar. Este test vigila que no vuelva a pasar.
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
CODIGO = [p for p in RAIZ.rglob("*")
          if p.suffix in {".py", ".go", ".js", ".sh"}
          and ".venv" not in p.parts and "tests" not in p.parts]

# una ruta absoluta al home del usuario metida en el código
RUTA_ABSOLUTA = re.compile(r"['\"](/home/[^'\"]+)['\"]")


def test_hay_codigo_que_revisar():
    assert len(CODIGO) > 20, "el test no está viendo el código del repo"


@pytest.mark.parametrize("archivo", CODIGO, ids=lambda p: str(p.relative_to(RAIZ)))
def test_ningun_archivo_apunta_fuera_del_repo(archivo):
    texto = archivo.read_text(encoding="utf-8", errors="replace")
    fuera = []
    for m in RUTA_ABSOLUTA.finditer(texto):
        ruta = m.group(1)
        if ruta.startswith(str(RAIZ)):
            continue                      # apuntar dentro del repo vale
        if "/.local/" in ruta or "/.cache/" in ruta:
            continue                      # intérpretes y modelos del sistema
        fuera.append(ruta)
    assert not fuera, (
        f"{archivo.relative_to(RAIZ)} apunta a rutas de fuera del repo: {fuera}. "
        f"Usa la variable TALLER_PROYECTO o el directorio actual.")


PYTHON = [p for p in CODIGO if p.suffix == ".py"]


@pytest.mark.parametrize("archivo", PYTHON, ids=lambda p: str(p.relative_to(RAIZ)))
def test_todo_el_python_es_sintacticamente_valido(archivo):
    """Un fallo de sintaxis en un script migrado no se nota hasta que alguien
    lo ejecuta meses después. Aquí se nota al momento."""
    import ast
    fuente = archivo.read_text(encoding="utf-8", errors="replace")
    try:
        ast.parse(fuente, filename=str(archivo))
    except SyntaxError as e:
        pytest.fail(f"{archivo.relative_to(RAIZ)} línea {e.lineno}: {e.msg}")
