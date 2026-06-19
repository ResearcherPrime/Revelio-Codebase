#!/usr/bin/env bash

set -e
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/4] Running scraping module"
bash "$ROOT_DIR/scraping/launcher.sh" full

echo "[2/4] Running protocol probing module"
bash "$ROOT_DIR/zstun_probing/launcher.sh" full

echo "[3/4] Running probing analysis module"
bash "$ROOT_DIR/zstun_probing_analysis/launcher.sh" full

echo "[4/4] Running STUN trace module"
bash "$ROOT_DIR/stun_trace/launcher.sh" full

echo "[DONE] Full pipeline completed"
