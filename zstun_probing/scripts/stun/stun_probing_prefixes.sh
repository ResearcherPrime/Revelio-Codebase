#!/usr/bin/env bash

set -e
set -u

# --- Paths ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Activate Python virtual environment
source "$REPO_ROOT/venv/bin/activate"

# --- Config & Arguments ---
if [[ $# -lt 2 ]]; then
    echo "Usage: ./stun_probing_prefixes.sh <grouped_countries.csv> <source_port> [mode]"
    exit 1
fi

MODE="${3:-full}"

# --- Dir paths ---
SCRAPING_DIR="$REPO_ROOT/scraping"
ZSTUN_PROBING_DIR="$REPO_ROOT/zstun_probing"

PREFIXES_DIR="$ZSTUN_PROBING_DIR/prefixes"
OUTPUT_DIR="$ZSTUN_PROBING_DIR/output"

PYTHON_SCRIPT="$ZSTUN_PROBING_DIR/scripts/merge_prefixes.py"

EXEC_LOG_DIR="$ZSTUN_PROBING_DIR/logs/exec"
TIME_LOG_DIR="$ZSTUN_PROBING_DIR/logs/time"

GROUPED_COUNTRIES="$1"

SOURCE_PORT="$2"

BLOCKLIST_FILE="$ZSTUN_PROBING_DIR/blocklist.txt"

# --- Quick/Full configuration ---
if [[ "$MODE" == "fast" ]]; then
    BANDWIDTH="500M"
    NUM_PROBES=10
    STUN_CONFIG="$SCRIPT_DIR/stun_pkts_quick.conf"
else
    BANDWIDTH="300M"
    NUM_PROBES=10
    STUN_CONFIG="$SCRIPT_DIR/stun_pkts.conf"
fi

# --- Functions ---

copy_and_aggregate_prefixes() {

    local scraping_output_file="$1"
    local aggregated_prefix_file="$2"

    local log_file="$EXEC_LOG_DIR/copy_prefixes.log"

    echo "=== Starting prefix processing and merging ==="

    echo "---------------------------------------------" >> "$log_file"

    echo "Processing: $scraping_output_file -> $aggregated_prefix_file"

    echo "Processing: $scraping_output_file -> $aggregated_prefix_file" \
        >> "$log_file"

    # Step 1: Extract prefixes from csv (ASN,Prefix)

    tail -n +2 "$scraping_output_file" \
        | cut -d',' -f2 \
        | sed 's/^ //' \
        > "$aggregated_prefix_file"

    # Step 2: Merge overlapping prefixes

    echo "Running prefix merge on: $aggregated_prefix_file"

    python3 "$PYTHON_SCRIPT" "$aggregated_prefix_file" \
        >> "$log_file" 2>&1

    echo "Finished: $aggregated_prefix_file"

    echo "---------------------------------------------" >> "$log_file"

    echo "=== Processing complete ==="
}

send_probes() {

    local input_prefix="$1"
    local output_dir="$2"
    local pkt_hex="$3"
    local pkt_type="$4"

    echo "$input_prefix $output_dir $pkt_type"

    zmap \
        -p 3478 \
        -M udp \
        --probe-args=hex:"$pkt_hex" \
        -w "$input_prefix" \
        -o "$output_dir/${pkt_type}.txt" \
        --output-fields=saddr,outer_saddr,success,classification,icmp_type,icmp_code \
        -s "$SOURCE_PORT" \
        -B "$BANDWIDTH" \
        --probes "$NUM_PROBES" \
        --blocklist-file "$BLOCKLIST_FILE"
}

log_duration() {

    local start_time=$1
    local end_time=$2
    local log_file=$3
    local country_name=$4

    local duration=$((end_time - start_time))

    local hours=$((duration / 3600))
    local minutes=$(((duration % 3600) / 60))
    local seconds=$((duration % 60))

    echo -e \
        "${country_name}: ${hours}h ${minutes}m ${seconds}s\n" \
        >> "$log_file"
}

# --- Main Logic ---

if [[ ! -f "$GROUPED_COUNTRIES" ]]; then
    echo "[ERROR] Grouped country file not found: $GROUPED_COUNTRIES"
    exit 1
fi

# --- Preprocessing ---

while IFS=',' read -r country _; do

    [[ -z "$country" ]] && continue

    COUNTRY_SCRAPING_OUTPUT="$SCRAPING_DIR/prefixes/${country}.csv"

    COUNTRY_PREFIXES="$PREFIXES_DIR/$country.txt"

    if [[ ! -f "$COUNTRY_SCRAPING_OUTPUT" ]]; then
        echo "[ERROR] Missing file: $COUNTRY_SCRAPING_OUTPUT"
        continue
    fi

    rm -rf \
        "$COUNTRY_PREFIXES" \
        "$OUTPUT_DIR/$country" \
        "$EXEC_LOG_DIR/$country" \
        "$TIME_LOG_DIR/$country"

    mkdir -p \
        "$OUTPUT_DIR/$country" \
        "$EXEC_LOG_DIR/$country" \
        "$TIME_LOG_DIR/$country"

    copy_and_aggregate_prefixes \
        "$COUNTRY_SCRAPING_OUTPUT" \
        "$COUNTRY_PREFIXES"

done < "$GROUPED_COUNTRIES"

# --- Packet Iteration ---

while IFS='=' read -r pkt_type pkt_hex; do

    # Skip comments and empty lines
    [[ -z "$pkt_type" || -z "$pkt_hex" ]] && continue
    [[ "$pkt_type" =~ ^#.*$ ]] && continue

    echo "STUN verification started for packet type: $pkt_type"

    while IFS=',' read -r country _; do

        [[ -z "$country" ]] && continue

        EXEC_LOG="$EXEC_LOG_DIR/${country}/${pkt_type}.log"

        TIME_LOG="$TIME_LOG_DIR/${country}/${pkt_type}.log"

        COUNTRY_PREFIXES="$PREFIXES_DIR/$country.txt"

        COUNTRY_OUTPUT_DIR="$OUTPUT_DIR/$country/$pkt_type"

        mkdir -p "$COUNTRY_OUTPUT_DIR"

        start=$(date +%s)

        echo -e \
            "STUN probes started for $country with packet type $pkt_type\n" \
            >> "$EXEC_LOG"

        send_probes \
            "$COUNTRY_PREFIXES" \
            "$COUNTRY_OUTPUT_DIR" \
            "$pkt_hex" \
            "$pkt_type"

        echo -e \
            "STUN probes completed for $country\n" \
            >> "$EXEC_LOG"

        end=$(date +%s)

        log_duration \
            "$start" \
            "$end" \
            "$TIME_LOG" \
            "$country"

    done < "$GROUPED_COUNTRIES"

done < "$STUN_CONFIG"

exit 0
