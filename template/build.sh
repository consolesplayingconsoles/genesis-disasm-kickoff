#!/usr/bin/env bash
# Regenerate the source from the ROM and the facts module, assemble it with AS and compare it with
# the ROM: MATCH or not. Writes the rebuild record (tracked) that tools/progress.py reads.
#   bash build.sh            (AS_PATH from .env; or set it in the environment)
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck disable=SC1091
# .env fills in what the environment does not set (AS_PATH and PYTHON alike)
_as="${AS_PATH:-}"; _py="${PYTHON:-}"
if [ -f .env ]; then . ./.env; fi
AS_PATH="${_as:-${AS_PATH:-}}"; PYTHON="${_py:-${PYTHON:-}}"
[ -n "${AS_PATH:-}" ] || { echo "[ERROR] no AS_PATH: put AS_PATH=\"/path/to/the folder with asl and p2bin\" in $PWD/.env (or export it)"; exit 1; }
[ -x "$AS_PATH/asl" ] && [ -x "$AS_PATH/p2bin" ] || { echo "[ERROR] no asl and p2bin in $AS_PATH"; exit 1; }
[ -f build/rom.bin ] || { echo "[ERROR] no build/rom.bin: run setup.sh with your ROM first"; exit 1; }
PY="${PYTHON:-python3}"
"$PY" -c 'import capstone' 2>/dev/null || { echo "[ERROR] $PY has no capstone: pip install capstone, or put PYTHON=\"/path/to/a python3 with it\" in $PWD/.env"; exit 1; }
rm -rf build/src
out="$("$PY" tools/rebuild.py build/rom.bin @TRACE@ build/src --as "$AS_PATH" --facts @FACTS@ @FACTS_ARGS@ --record @RECORD@)"
echo "$out"
case "$out" in *"identical (SHA-1"*) echo MATCH ;; *) echo "NO MATCH"; exit 1 ;; esac
