#!/usr/bin/env bash
# This code recreates the figures from the paper using the provided datasets.

set -e
set -u

# --------------------------------------------------
# Paths
# --------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$REPO_ROOT/venv/bin/activate"

if [[ ! -d "$SCRIPT_DIR/input" ]] || ! find "$SCRIPT_DIR/input" -type f ! -name "*.tar.xz" -print -quit | grep -q .; then
    echo "[ERROR] Input data does not exist. Please extract the input dataset first using extraction.sh"
    exit 1
fi

echo "[1/11] Recreating Figure 3"
python3 "$SCRIPT_DIR/figure3_paper_box_plot.py"

echo "[2/11] Recreating Figure 4"
python3 "$SCRIPT_DIR/figure4_churn_stun_count_percentages_plot.py"

echo "[3/11] Recreating Figure 5"
python3 "$SCRIPT_DIR/figure5_uae_udp_deviation.py"

echo "[4/11] Recreating Figure 6"
python3 "$SCRIPT_DIR/figure6_sa_udp_deviation.py"

echo "[5/11] Recreating Figure 7"
python3 "$SCRIPT_DIR/figure7_uae_no_response_deviation.py"

echo "[6/11] Recreating Figure 8"
python3 "$SCRIPT_DIR/figure8_myanmar_icmp_drop.py"

echo "[7/11] Recreating Figure 9"
python3 "$SCRIPT_DIR/figure9_uae_icmp_ttl_deviation.py"

echo "[8/11] Recreating Figure 10"
python3 "$SCRIPT_DIR/figure10_uae_icmp_dest_unreachable_deviation.py"

echo "[9/11] Processing Figure 12 data"
python3 "$SCRIPT_DIR/figure12_script_b_iterate_categorisation.py"
python3 "$SCRIPT_DIR/figure12_script_c_calculate_percentage.py"

echo "[10/11] Recreating Figure 12"
python3 "$SCRIPT_DIR/figure12_script_d_plot_heatmap.py"

echo "[11/11] Recreating Table-3"
python3 "$SCRIPT_DIR/table3_middlebox_statistics.py"

echo "[DONE] Paper graphs recreated successfully"
