#!/bin/bash

set -e

set -u

echo "=========================================="
echo "Claim C3: Middlebox Detection"
echo "Run Demo (default = United Arab Emirates)"
echo "=========================================="


start=$(date +%s)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COUNTRY="${1:-United_Arab_Emirates}" 
APP_NAME="${2:-whatsapp}"

# ------------------------------------------------------------------
# Step 1: Prepare claim-specific configuration
# ------------------------------------------------------------------

echo "[1/4] Preparing C2 configuration"

cp "$SCRIPT_DIR/config/scraping/${COUNTRY}.csv" "$REPO_ROOT/scraping/prefixes/${COUNTRY}.csv"

echo "$COUNTRY" > "$REPO_ROOT/zstun_probing/input.csv"
echo "$COUNTRY" > "$REPO_ROOT/zstun_probing_analysis/input.csv"
echo "$COUNTRY" > "$REPO_ROOT/stun_trace/input.csv"

# Copy probe definitions (P1, P2, P3)

# Select the diff file based on application filtered in that country
if [[ "$APP_NAME" == "whatsapp" ]]; then
    cp "$SCRIPT_DIR"/config/zstun_probing/stun_pkts.conf.whatsapp "$REPO_ROOT/zstun_probing/scripts/stun/stun_pkts.conf"
    cp "$SCRIPT_DIR"/config/zstun_probing_analysis/app_labels.conf.whatsapp "$REPO_ROOT/zstun_probing_analysis/app_labels.conf"

elif [[ "$APP_NAME" == "telegram" ]]; then
    cp "$SCRIPT_DIR"/config/zstun_probing/stun_pkts.conf.telegram "$REPO_ROOT/zstun_probing/scripts/stun/stun_pkts.conf"
    cp "$SCRIPT_DIR"/config/zstun_probing_analysis/app_labels.conf.telegram "$REPO_ROOT/zstun_probing_analysis/app_labels.conf"

elif [[ "$APP_NAME" == "signal" ]]; then
    cp "$SCRIPT_DIR"/config/zstun_probing/stun_pkts.conf.signal "$REPO_ROOT/zstun_probing/scripts/stun/stun_pkts.conf"
    cp "$SCRIPT_DIR"/config/zstun_probing_analysis/app_labels.conf.signal "$REPO_ROOT/zstun_probing_analysis/app_labels.conf"

elif [[ "$APP_NAME" == "messenger" ]]; then
    cp "$SCRIPT_DIR"/config/zstun_probing/stun_pkts.conf.messenger "$REPO_ROOT/zstun_probing/scripts/stun/stun_pkts.conf"
    cp "$SCRIPT_DIR"/config/zstun_probing_analysis/app_labels.conf.messenger "$REPO_ROOT/zstun_probing_analysis/app_labels.conf"

fi

# ------------------------------------------------------------------
# Step 2: Probe the entire country using zstun
# ------------------------------------------------------------------

echo "[2/4] Running Revelio measurements"

cd "$REPO_ROOT"

bash zstun_probing/launcher.sh

# ------------------------------------------------------------------
# Step 3: Generate response-distribution graphs
# ------------------------------------------------------------------

echo "[3/4] Generating differential probing graphs"

bash zstun_probing_analysis/launcher.sh

# ------------------------------------------------------------------
# Step 4: Generate response-distribution graphs
# ------------------------------------------------------------------

echo "[4/4] Generating differential probing graphs"

bash stun_trace/launcher.sh

echo ""
echo "=========================================="
echo "Claim C3 Completed"
echo "=========================================="

end=$(date +%s)
duration=$((end - start))
hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))

echo ""
echo "Total Time: ${hours}h ${minutes}m ${seconds}s"
echo ""
