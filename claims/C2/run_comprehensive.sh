#!/bin/bash

set -e

set -u

echo "=========================================="
echo "Claim C2: VoIP Censorship Detection"
echo "Run Comprehensive for all 19 coutnries"
echo "=========================================="


start=$(date +%s)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ------------------------------------------------------------------
# Step 1: Prepare claim-specific configuration
# ------------------------------------------------------------------

echo "[1/3] Preparing C2 configuration"

cp "$SCRIPT_DIR"/config/scraping/* "$REPO_ROOT/scraping/prefixes/"

cp "$SCRIPT_DIR/config/zstun_probing/stun_pkts.conf" "$REPO_ROOT/zstun_probing/scripts/stun/stun_pkts.conf"
cp "$SCRIPT_DIR/config/zstun_probing/input.csv" "$REPO_ROOT/zstun_probing/input.csv"

cp "$SCRIPT_DIR/config/zstun_probing_analysis/app_labels.conf" "$REPO_ROOT/zstun_probing_analysis/app_labels.conf"
cp "$SCRIPT_DIR/config/zstun_probing_analysis/input.csv" "$REPO_ROOT/zstun_probing_analysis/input.csv"

# ------------------------------------------------------------------
# Step 2: Probe filtered destinations
# ------------------------------------------------------------------

echo "[2/3] Running Revelio measurements"

cd "$REPO_ROOT"

bash zstun_probing/launcher.sh

# ------------------------------------------------------------------
# Step 3: Generate response-distribution graphs
# ------------------------------------------------------------------

echo "[3/3] Generating differential probing graphs"

bash zstun_probing_analysis/launcher.sh

echo ""
echo "=========================================="
echo "Claim C2 Completed"
echo "=========================================="

end=$(date +%s)
duration=$((end - start))
hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))

echo ""
echo "Total Time: ${hours}h ${minutes}m ${seconds}s"
echo ""
