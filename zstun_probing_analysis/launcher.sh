#!/usr/bin/env bash

set -e
set -u

# --------------------------------------------------
# Paths
# --------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_CONFIG="$SCRIPT_DIR/app_labels.conf"

# Activate Python virtual environment
source "$REPO_ROOT/venv/bin/activate"

# --------------------------------------------------
# Mode
# --------------------------------------------------

MODE="${1:-full}"

# --------------------------------------------------
# Input configuration
# --------------------------------------------------

if [[ "$MODE" == "fast" ]]; then

    echo -e "\n[INFO] Running ZSTUN probing analysis in FAST mode\n"

    INPUT_FILE="$SCRIPT_DIR/input_fast.csv"

else

    echo -e "\n[INFO] Running ZSTUN probing analysis in FULL mode\n"

    INPUT_FILE="$SCRIPT_DIR/input.csv"

fi

# --------------------------------------------------
# Validation
# --------------------------------------------------

if [[ ! -f "$INPUT_FILE" ]]; then
    echo "[ERROR] Missing file: $INPUT_FILE"
    exit 1
fi

# --------------------------------------------------
# Output directories
# --------------------------------------------------

OUTPUT_DIR="$SCRIPT_DIR/output"

mkdir -p "$OUTPUT_DIR"

# --------------------------------------------------
# Main execution
# --------------------------------------------------

while IFS=',' read -r country _; do

    [[ -z "$country" ]] && continue

    echo -e "\n[INFO] Running analysis for $country\n"

    # --------------------------------------------------
    # UDP behaviour deviation analysis
    # --------------------------------------------------

    python3 \
        "$SCRIPT_DIR/udp_behaviour_deviation.py" \
        "$country" \
        "$APP_CONFIG"

    # --------------------------------------------------
    # ICMP behaviour deviation analysis
    # --------------------------------------------------

    if [[ "$country" != "United_Arab_Emirates" ]]; then

        python3 \
            "$SCRIPT_DIR/icmp_behaviour_deviation.py" \
            "$country" \
            -1 \
            "$APP_CONFIG"

    else

        python3 \
            "$SCRIPT_DIR/icmp_behaviour_deviation.py" \
            "$country" \
            11 \
            "$APP_CONFIG"

        python3 \
            "$SCRIPT_DIR/icmp_behaviour_deviation.py" \
            "$country" \
            3 \
            "$APP_CONFIG"

        python3 \
            "$SCRIPT_DIR/icmp_behaviour_deviation.py" \
            "$country" \
            5 \
            "$APP_CONFIG"

        python3 \
            "$SCRIPT_DIR/merge_uae_icmp_results.py" \
            "$country" \
            "$APP_CONFIG"

    fi

    # --------------------------------------------------
    # No-response behaviour deviation analysis
    # --------------------------------------------------

    python3 \
        "$SCRIPT_DIR/no_response_behaviour_deviation.py" \
        "$country" \
        "$APP_CONFIG"

done < "$INPUT_FILE"

echo -e "\n[INFO] ZSTUN probing analysis completed\n"
