#!/usr/bin/env bash
# This code is to reproduce the graphs presented in the paper

set -e
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRAPHS_DIR="$ROOT_DIR/graphs_from_paper"

echo "[1] Extracting graph datasets"
bash "$ROOT_DIR/extraction.sh"

echo "[2] Recreating graphs"
bash "$GRAPHS_DIR/launcher.sh"

echo "[DONE] Paper graphs recreated successfully"
