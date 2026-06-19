#!/usr/bin/env bash

set -e
set -u

# --------------------------------------------------
# Paths
# --------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$REPO_ROOT/venv/bin/activate"

ASNS_DIR="$SCRIPT_DIR/asns"

PREFIX_DIR="$SCRIPT_DIR/prefixes"

TIME_LOG_DIR="$SCRIPT_DIR/logs/time"

mkdir -p \
    "$ASNS_DIR" \
    "$PREFIX_DIR" \
    "$TIME_LOG_DIR"

# --------------------------------------------------
# Arguments
# --------------------------------------------------

if [[ $# -lt 2 ]]; then

    echo "Usage:"
    echo "./batch_prefix_scrapper.sh <country_file> <offset> [fast]"

    exit 1
fi

INPUT_FILE="$1"

OFFSET="$2"

MODE="${3:-full}"

LOG_NAME="$(basename "${INPUT_FILE%.*}")"

START=$(date +%s)

# --------------------------------------------------
# Validation
# --------------------------------------------------

if [[ ! -f "$INPUT_FILE" ]]; then

    echo "[ERROR] File not found:"
    echo "$INPUT_FILE"

    exit 1
fi

# --------------------------------------------------
# Prefix scraping loop
# --------------------------------------------------

while IFS=',' read -r COUNTRY _; do

    COUNTRY="${COUNTRY//$'\r'/}"

    [[ -z "$COUNTRY" ]] && continue

    echo
    echo "[INFO] Prefix scraping started for $COUNTRY"
    echo

    CMD=(
        python3
        "$SCRIPT_DIR/prefix_scrapper.py"
        "$ASNS_DIR/${COUNTRY}"
        "$LOG_NAME"
        "$OFFSET"
    )

    if [[ "$MODE" == "fast" ]]; then
        CMD+=("fast")
    fi

    "${CMD[@]}"

    echo
    echo "[INFO] Prefixes scraped:"
    echo "$PREFIX_DIR/${COUNTRY}.csv"
    echo

done < "$INPUT_FILE"

# --------------------------------------------------
# Timing
# --------------------------------------------------

END=$(date +%s)

DURATION=$((END - START))

HOURS=$((DURATION / 3600))

MINUTES=$(((DURATION % 3600) / 60))

SECONDS=$((DURATION % 60))

echo \
    -e "\nTotal Time: ${HOURS}h ${MINUTES}m ${SECONDS}s\n" \
    >> "$TIME_LOG_DIR/prefix_scraping_${LOG_NAME}.log"

exit 0
