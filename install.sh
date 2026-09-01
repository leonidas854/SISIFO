#!/usr/bin/env bash
# Instala SISIFO: compila el binario, prepara el intérprete de Python y enlaza
# las skills a nivel de usuario para que estén en CUALQUIER proyecto.
#
# Todo lo instalado apunta a este repo. Borrar una carpeta de trabajo —o
# cualquier otro proyecto de tareas/— no toca el sistema.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_USUARIO="$HOME/.local/bin"
SKILLS_USUARIO="$HOME/.claude/skills"

echo "SISIFO · instalando desde $RAIZ"

# ── 1. comprobaciones previas ────────────────────────────────────────────
for req in go python3; do
  command -v "$req" >/dev/null || { echo "  falta $req"; exit 1; }
done

# ── 2. intérprete Python con las dependencias ────────────────────────────
if [ ! -x "$RAIZ/.venv/bin/python" ]; then
  echo "  creando .venv (hereda los paquetes del sistema)"
  python3 -m venv --system-site-packages "$RAIZ/.venv"
fi
"$RAIZ/.venv/bin/pip" install -q --upgrade pip
"$RAIZ/.venv/bin/pip" install -q citeproc-py citeproc-py-styles requests pyyaml pytest
echo "  intérprete listo"

# ── 3. dependencias de Node (PPTX con gráficos nativos) ──────────────────
if command -v npm >/dev/null; then
  ( cd "$RAIZ" && npm install --silent --no-audit --no-fund )
  echo "  pptxgenjs listo (gráficos y notas nativas en PPTX)"
else
  echo "  npm no está: el PPTX se generará con python-pptx (sin gráficos nativos)"
fi

# ── 4. binario Go ────────────────────────────────────────────────────────
mkdir -p "$RAIZ/bin"
( cd "$RAIZ" && go build -o bin/sisifo ./cmd/sisifo )
echo "  binario compilado: bin/sisifo"

# ── 5. el comando, disponible desde cualquier carpeta ────────────────────
mkdir -p "$BIN_USUARIO"
ln -sf "$RAIZ/bin/sisifo" "$BIN_USUARIO/sisifo"
ln -sf "$RAIZ/bin/sisifo" "$BIN_USUARIO/taller"   # alias del nombre anterior
echo "  enlazado: $BIN_USUARIO/sisifo  (y 'taller' como alias)"
case ":$PATH:" in
  *":$BIN_USUARIO:"*) ;;
  *) echo "  AVISO: $BIN_USUARIO no está en el PATH; añádelo a ~/.zshrc" ;;
esac

# ── 6. skills a nivel de usuario: valen en todos los proyectos ───────────
mkdir -p "$SKILLS_USUARIO"
for s in "$RAIZ"/skills/*/; do
  nombre="$(basename "$s")"
  ln -sfn "${s%/}" "$SKILLS_USUARIO/$nombre"
  echo "  skill enlazada: $nombre"
done

echo
echo "listo. Comprueba el entorno con:  sisifo doctor"
