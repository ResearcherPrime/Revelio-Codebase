#!/usr/bin/env bash

set -e
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/4] Running scraping module"
bash "$ROOT_DIR/scraping/launcher.sh" fast

echo "[2/4] Running protocol probing module"
bash "$ROOT_DIR/zstun_probing/launcher.sh" fast

echo "[3/4] Running probing analysis module"
bash "$ROOT_DIR/zstun_probing_analysis/launcher.sh" fast

echo "[4/4] Running STUN trace module"
bash "$ROOT_DIR/stun_trace/launcher.sh" fast

echo "[DONE] Fast-mode pipeline completed"
