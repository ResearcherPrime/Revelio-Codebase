#!/bin/bash

set -e
set -u

echo "=========================================="
echo "Claim C1: Zstun Discovery Evaluation"
echo "Demo Run (United Arab Emirates)"
echo "=========================================="

start=$(date +%s)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ------------------------------------------------------------------
# Step 1: Prepare claim-specific configuration
# ------------------------------------------------------------------

echo "[1/5] Preparing C1 demo configuration"

cp "$SCRIPT_DIR"/config/scraping/demo/* "$REPO_ROOT/scraping/"

cp "$SCRIPT_DIR"/config/port_scanning/demo/* "$REPO_ROOT/port_scanning/"

cp "$SCRIPT_DIR/config/zstun_probing/demo/stun_pkts_quick.conf" "$REPO_ROOT/zstun_probing/scripts/stun/stun_pkts_quick.conf"

# ------------------------------------------------------------------
# Step 2: Scrape ASNs and prefixes
# ------------------------------------------------------------------

echo "[2/5] Collecting UAE prefixes"

cd "$REPO_ROOT"

bash scraping/launcher.sh fast

# ------------------------------------------------------------------
# Step 3: UDP/3478 and TCP/3478 scan
# ------------------------------------------------------------------

echo "[3/5] Running UDP and TCP 3478 port scan"

bash port_scanning/launcher.sh

# ------------------------------------------------------------------
# Step 4: Zstun scan with vanilla STUN probes
# ------------------------------------------------------------------

echo "[4/5] Running Zstun validation"

bash zstun_probing/launcher.sh fast

# ------------------------------------------------------------------
# Generate summary
# ------------------------------------------------------------------

echo "[5/5] Running Zstun vs. UDP/TCP summary generation"

python3 claims/C1/generate_summary.py

echo ""
echo "=========================================="
echo "Claim C1 Completed"
echo "=========================================="

end=$(date +%s)
duration=$((end - start))
hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))

echo "\nTotal Time: ${hours}h ${minutes}m ${seconds}s\n"
