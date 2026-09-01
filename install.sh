#!/usr/bin/env bash
# Instala el taller: compila el binario, prepara el intérprete y enlaza las
# skills a nivel de usuario para que estén disponibles en CUALQUIER proyecto.
#
# Todo lo instalado apunta aquí. Borrar una carpeta de trabajo no toca nada.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_USUARIO="$HOME/.local/bin"
SKILLS_USUARIO="$HOME/.claude/skills"

echo "taller · instalando desde $RAIZ"

# ── 1. intérprete Python con las dependencias del taller ─────────────────
if [ ! -x "$RAIZ/.venv/bin/python" ]; then
  echo "  creando .venv (hereda los paquetes del sistema)"
  python3 -m venv --system-site-packages "$RAIZ/.venv"
fi
"$RAIZ/.venv/bin/pip" install -q --upgrade pip
"$RAIZ/.venv/bin/pip" install -q citeproc-py citeproc-py-styles requests pyyaml
echo "  intérprete listo"

# ── 2. binario Go ────────────────────────────────────────────────────────
mkdir -p "$RAIZ/bin"
( cd "$RAIZ" && go build -o bin/taller ./cmd/taller )
echo "  binario compilado: bin/taller"

# ── 3. el comando, disponible desde cualquier carpeta ────────────────────
mkdir -p "$BIN_USUARIO"
ln -sf "$RAIZ/bin/taller" "$BIN_USUARIO/taller"
echo "  enlazado: $BIN_USUARIO/taller"
case ":$PATH:" in
  *":$BIN_USUARIO:"*) ;;
  *) echo "  AVISO: $BIN_USUARIO no está en el PATH; añádelo a ~/.zshrc" ;;
esac

# ── 4. skills a nivel de usuario: valen en todos los proyectos ───────────
mkdir -p "$SKILLS_USUARIO"
for s in "$RAIZ"/skills/*/; do
  nombre="$(basename "$s")"
  ln -sfn "${s%/}" "$SKILLS_USUARIO/$nombre"
  echo "  skill enlazada: $nombre"
done

echo
echo "listo. Comprueba el entorno con:  taller doctor"
