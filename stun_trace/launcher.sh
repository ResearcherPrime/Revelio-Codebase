#!/usr/bin/env bash

set -e
set -u

# --------------------------------------------------
# Paths
# --------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TRACE_OUTPUT_ROOT="$SCRIPT_DIR/trace_output"

ANALYSIS_ROOT="$REPO_ROOT/zstun_probing_analysis/output"

INPUT_FILE="$SCRIPT_DIR/input.csv"

source "$REPO_ROOT/venv/bin/activate"

# rm -rf "$TRACE_OUTPUT_ROOT"

# mkdir -p "$TRACE_OUTPUT_ROOT"

# --------------------------------------------------
# Arguments
# --------------------------------------------------

MODE="${1:-fast}"

# --------------------------------------------------
# Validation
# --------------------------------------------------

if [[ "$MODE" != "fast" && "$MODE" != "full" ]]; then

    echo "[ERROR] MODE must be either:"
    echo "fast OR full"

    exit 1
fi

# --------------------------------------------------
# FAST mode
# --------------------------------------------------

if [[ "$MODE" == "fast" ]]; then

    COUNTRY="United_Arab_Emirates"

    APP_NAME="whatsapp"

    FILTERED_IPS_FILE="$ANALYSIS_ROOT/$COUNTRY/no_response_deviation/filtered_ips_WhatsApp.txt"

    TRACE_OUTPUT_DIR="$TRACE_OUTPUT_ROOT/$COUNTRY/no_response_deviation"
    
    APP_TRACE_OUTPUT_DIR="$TRACE_OUTPUT_DIR/$APP_NAME"
    
    mkdir -p "$APP_TRACE_OUTPUT_DIR"

    if [[ ! -f "$FILTERED_IPS_FILE" ]]; then

        echo "[ERROR] Missing filtered IP file:"
        echo "$FILTERED_IPS_FILE"

        exit 1
    fi

    mapfile -t TARGET_IPS < <(
        shuf -n 10 "$FILTERED_IPS_FILE"
    )

    echo "[FAST] Running traceroutes for 10 random UAE IPs"

    for TARGET_IP in "${TARGET_IPS[@]}"; do

        [[ -z "$TARGET_IP" ]] && continue

        echo "[FAST] Vanilla STUN trace -> $TARGET_IP"

        python3 "$SCRIPT_DIR/voip_traceroute.py" \
            -dip "$TARGET_IP" \
            -pcap -1 \
            > "$APP_TRACE_OUTPUT_DIR/${TARGET_IP}_p1.txt" 2>&1

        echo "[FAST] WhatsApp trace -> $TARGET_IP"

        python3 "$SCRIPT_DIR/voip_traceroute.py" \
            -dip "$TARGET_IP" \
            -app "$APP_NAME" \
            > "$APP_TRACE_OUTPUT_DIR/${TARGET_IP}_p2.txt" 2>&1

    done

    PREFIX_FILE="$REPO_ROOT/scraping/prefixes/$COUNTRY.csv"

    python3 "$SCRIPT_DIR/eval_trace_no_response_deviation.py" "$TRACE_OUTPUT_DIR" "$PREFIX_FILE"

    echo "[DONE] FAST tracing completed"

    exit 0
fi

# --------------------------------------------------
# FULL mode
# --------------------------------------------------

if [[ ! -f "$INPUT_FILE" ]]; then

    echo "[ERROR] Missing input file:"
    echo "$INPUT_FILE"

    exit 1
fi

while IFS=',' read -r COUNTRY _; do

    COUNTRY="${COUNTRY//$'\r'/}"

    [[ -z "$COUNTRY" ]] && continue

    echo "[FULL] Processing country: $COUNTRY"

    COUNTRY_ANALYSIS_DIR="$ANALYSIS_ROOT/$COUNTRY"

    if [[ ! -d "$COUNTRY_ANALYSIS_DIR" ]]; then

        echo "[WARNING] Missing analysis directory:"
        echo "$COUNTRY_ANALYSIS_DIR"

        continue
    fi

    for DEVIATION_DIR in "$COUNTRY_ANALYSIS_DIR"/*_deviation; do

        [[ ! -d "$DEVIATION_DIR" ]] && continue

        DEVIATION_NAME="$(basename "$DEVIATION_DIR")"

        echo "[FULL] Processing deviation type: $DEVIATION_NAME"

        TRACE_OUTPUT_DIR="$TRACE_OUTPUT_ROOT/$COUNTRY/$DEVIATION_NAME"

        mkdir -p "$TRACE_OUTPUT_DIR"

        for FILTERED_IPS_FILE in "$DEVIATION_DIR"/filtered_ips_*.txt; do

            [[ ! -f "$FILTERED_IPS_FILE" ]] && continue

            APP_LABEL="$(
                basename "$FILTERED_IPS_FILE" \
                | sed 's/filtered_ips_//' \
                | sed 's/.txt//'
            )"

            APP_NAME="$(
                echo "$APP_LABEL" \
                | tr '[:upper:]' '[:lower:]'
            )"

            APP_TRACE_OUTPUT_DIR="$TRACE_OUTPUT_DIR/$APP_NAME"
            mkdir -p "$APP_TRACE_OUTPUT_DIR"

            echo "[FULL] Running traces for:"
            echo "       App        -> $APP_NAME"
            echo "       Deviation  -> $DEVIATION_NAME"

            while IFS= read -r TARGET_IP; do

                [[ -z "$TARGET_IP" ]] && continue

                echo "[FULL] Vanilla STUN trace -> $TARGET_IP"

                python3 "$SCRIPT_DIR/voip_traceroute.py" \
                    -dip "$TARGET_IP" \
                    -pcap -1 \
                    > "$APP_TRACE_OUTPUT_DIR/${TARGET_IP}_p1.txt" 2>&1

                echo "[FULL] ${APP_NAME} trace -> $TARGET_IP"

                python3 "$SCRIPT_DIR/voip_traceroute.py" \
                    -dip "$TARGET_IP" \
                    -app "$APP_NAME" \
                    > "$APP_TRACE_OUTPUT_DIR/${TARGET_IP}_p2.txt" 2>&1

            done < "$FILTERED_IPS_FILE"

            PREFIX_FILE="$REPO_ROOT/scraping/prefixes/$COUNTRY.csv"

            python3 "$SCRIPT_DIR/eval_trace_$DEVIATION_NAME.py" "$TRACE_OUTPUT_DIR" "$PREFIX_FILE"

        done

    done

done < "$INPUT_FILE"

echo "[DONE] FULL tracing completed"
