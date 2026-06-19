#!/usr/bin/env bash

set -e
set -u

# --------------------------------------------------
# Paths
# --------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Activate Python virtual environment
source "$REPO_ROOT/venv/bin/activate"

# --------------------------------------------------
# Paths
# --------------------------------------------------

OUTPUT_DIR="$SCRIPT_DIR/output"

GROUPING_SCRIPT="$SCRIPT_DIR/groupby.py"

# --------------------------------------------------
# Validation
# --------------------------------------------------

if [[ ! -d "$OUTPUT_DIR" ]]; then
    echo "[ERROR] Missing output directory: $OUTPUT_DIR"
    exit 1
fi

if [[ ! -f "$GROUPING_SCRIPT" ]]; then
    echo "[ERROR] Missing script: $GROUPING_SCRIPT"
    exit 1
fi

# --------------------------------------------------
# Timer
# --------------------------------------------------

start_time=$(date +%s)

echo "[START] Compression started"

# --------------------------------------------------
# Iterate over countries
# --------------------------------------------------

for country_folder in "$OUTPUT_DIR"/*/; do

    [[ ! -d "$country_folder" ]] && continue

    country_name=$(basename "$country_folder")

    echo "[COUNTRY] $country_name"

    # --------------------------------------------------
    # Iterate over app folders
    # --------------------------------------------------

    for port_scan_output in "$country_folder"/*.txt; do

        port_scan_name=$(basename "$port_scan_output")

        infile="$port_scan_output"

        tmp="$port_scan_output.tmp"

        if [[ ! -f "$infile" ]]; then
            echo "[SKIP] Missing file: $infile"
            continue
        fi

        echo "[PROCESS] $country_name / $port_scan_name"

        # --------------------------------------------------
        # Compress grouped rows
        # --------------------------------------------------

        if ! python3 \
            "$GROUPING_SCRIPT" \
            "$infile" \
            "$tmp"; then

            echo "[ERROR] groupby.py failed for $infile"

            exit 1
        fi

        # --------------------------------------------------
        # Replace original file
        # --------------------------------------------------

        mv "$tmp" "$infile"

        echo "[DONE] Compressed: $infile"

    done

done

# --------------------------------------------------
# Timing summary
# --------------------------------------------------

end_time=$(date +%s)

elapsed=$((end_time - start_time))

hours=$((elapsed / 3600))
mins=$(((elapsed % 3600) / 60))
secs=$((elapsed % 60))

printf \
"\n[DONE] Compression completed in %02d:%02d:%02d\n" \
"$hours" \
"$mins" \
"$secs"
