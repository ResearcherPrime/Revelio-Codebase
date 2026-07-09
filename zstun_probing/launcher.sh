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
# Configuration
# --------------------------------------------------

CONFIG="$SCRIPT_DIR/launcher.conf"

PROTOCOL=$(grep '^protocol=' "$CONFIG" | cut -d'=' -f2 | tr -d '[:space:]')        # Select the type of scanning - stun, echo

WEBHOOK_URL=$(grep '^webhook=' "$CONFIG" | cut -d'=' -f2- | tr -d '[:space:]')     # Enter a webhook url to get updates during ongoing scraping as notifications

MODE="${1:-full}"

# --------------------------------------------------
# Dir paths
# --------------------------------------------------

TMPDIR="$SCRIPT_DIR/logs/temp"

PREFIX_SCRAPE_DIR="$REPO_ROOT/scraping/prefixes"

EXEC_LOG="$SCRIPT_DIR/logs/exec"
TIME_LOG="$SCRIPT_DIR/logs/time"

OUTPUT_DIR="$SCRIPT_DIR/output"
PREFIXES_DIR="$SCRIPT_DIR/prefixes"

INPUT_FILE="$SCRIPT_DIR/input.csv"

FAST_INPUT_FILE="$SCRIPT_DIR/input_fast.csv"

# --------------------------------------------------
# Validation
# --------------------------------------------------

if [[ -z "$PROTOCOL" ]]; then
  echo "[ERROR] Protocol to be scanned amongst stun or echo is missing in $CONFIG"
  exit 1
fi

# --------------------------------------------------
# Sending update notification using webhook
# --------------------------------------------------

send_notification() {

    local payload="$1"

    # If webhook URL is not configured, print the notification locally.

    if [[ -z "$WEBHOOK_URL" ]]; then
        # echo -e "\n[INFO] WEBHOOK_URL is not configured."
        # echo "[INFO] Enter your own webhook URL to receive notifications."
        echo -e "[INFO] Notification payload:\n$payload\n"
        return
    fi

    if ! curl -s \
        -H 'Content-Type: application/json' \
        -d "$payload" \
        "$WEBHOOK_URL" > /dev/null 2>&1; then

        echo -e "\n[ERROR] Webhook notification failed\n"
    fi
}

# --------------------------------------------------
# Counters
# --------------------------------------------------

NUM_PANES=4
NUM_SESSIONS=2
declare -a PANE_LIST=()

# Read file into array
mapfile -t lines < "$INPUT_FILE"

# Check if array is empty
if [ ${#lines[@]} -eq 0 ]; then
    echo -e "\n[ERROR] File '$INPUT_FILE' is empty"
    exit 1
fi

# --------------------------------------------------
# Create tmux sessions
# --------------------------------------------------

for ((i=1; i<=NUM_SESSIONS; i++))                                                   # Splitting the tmux into individual panes to run parallel scripts
do
    # Create new tmux session

    if tmux has-session -t "zstun_session_$i" 2>/dev/null; then
        tmux kill-session -t "zstun_session_$i"
    fi

    tmux new-session -d -s "zstun_session_$i"
    
    # Split window into four panes in a 2x2 grid

    tmux split-window -h -t "zstun_session_$i:0.0"

    tmux split-window -v -t "zstun_session_$i:0.0"

    tmux split-window -v -t "zstun_session_$i:0.1"

    # Store pane IDs

    PANE_LIST+=(
        "zstun_session_$i:0.0"
        "zstun_session_$i:0.1"
        "zstun_session_$i:0.2"
        "zstun_session_$i:0.3"
    )

    # Retile panes for even 2x2 grid distribution

    tmux select-layout -t "zstun_session_$i:0" tiled
    
    # Select first pane

    tmux select-pane -t "zstun_session_$i:0.0"
done

# --------------------------------------------------
# Remove existing directory and prepare for new results
# --------------------------------------------------

rm -rf \
    "$EXEC_LOG" \
    "$TIME_LOG" \
    "$TMPDIR" \
    "$OUTPUT_DIR" \
    "$PREFIXES_DIR"

mkdir -p \
    "$EXEC_LOG" \
    "$TIME_LOG" \
    "$TMPDIR" \
    "$OUTPUT_DIR" \
    "$PREFIXES_DIR"

SOURCE_PORTS=(
    "42000-42010"
    "44000-44010"
    "46000-46010"
    "48000-48010"
    "52000-52010"
    "54000-54010"
    "56000-56010"
    "58000-58010"
)

# --------------------------------------------------
# Function to divide countries based on IP size
# --------------------------------------------------
balance_groups() {

    local log="$EXEC_LOG/balanced_groups.log"

    local groups=8

    # --------------------------------------------------
    # Step 1: Initialize totals and group storage
    # --------------------------------------------------

    local group_size=()

    local groups_array=()

    for i in $(seq 0 $((groups - 1))); do

        group_size[$i]=0

        groups_array[$i]=""

    done

    local tmpfile

    tmpfile=$(mktemp)

    # --------------------------------------------------
    # Step 2: Count IPs per country file
    # --------------------------------------------------

    echo -e "\n[INFO] Counting IPs per country..." \
        >> "$log"

    while read -r country; do

        [[ -z "$country" ]] && continue

        local filepath="${PREFIX_SCRAPE_DIR}/${country}.csv"

        local count=0

        if [[ -f "$filepath" ]]; then

            local filtered_file

            filtered_file=$(mktemp)

            tail -n +2 "$filepath" \
                | cut -d',' -f2 \
                | sed 's/^ //' \
                > "$filtered_file"

            count=$(
                python3 \
                "$SCRIPT_DIR/scripts/count_ips.py" \
                "$filtered_file"
            )

            rm "$filtered_file"

        else

            echo -e \
                "\n[ERROR] Missing file: $filepath\n" \
                >> "$log"

            count=0
        fi

        echo -e \
            "$country -> $count IPs" \
            >> "$log"

        echo "$count $country" >> "$tmpfile"

    done < "$INPUT_FILE"

    # --------------------------------------------------
    # Step 3: Sort countries by IP count
    # --------------------------------------------------

    sort -nr "$tmpfile" -o "$tmpfile"

    # --------------------------------------------------
    # Step 4: Assign countries to groups
    # --------------------------------------------------

    echo -e \
        "\n[INFO] Assigning countries to groups..." \
        >> "$log"

    while read -r count file; do

        local min_idx=0

        local min_val=${group_size[0]}

        for i in $(seq 1 $((groups - 1))); do

            if (( group_size[i] < min_val )); then

                min_val=${group_size[i]}

                min_idx=$i

            fi

        done

        groups_array[$min_idx]="${groups_array[$min_idx]} $file"

        group_size[$min_idx]=$(( group_size[$min_idx] + count ))

        echo -e \
            "[INFO] Placed $file ($count IPs) into Group $min_idx" \
            >> "$log"

    done < "$tmpfile"

    rm "$tmpfile"

    # --------------------------------------------------
    # Step 5: Write group files
    # --------------------------------------------------

    local outfiles=()

    for i in $(seq 0 $((groups - 1))); do

        local outfile="$SCRIPT_DIR/group$i.txt"

        outfiles+=("$outfile")

        echo "${groups_array[$i]}" \
            | tr ' ' '\n' \
            | grep -v '^$' \
            | sort -r \
            > "$outfile"

    done

    # --------------------------------------------------
    # Step 6: Summary
    # --------------------------------------------------

    echo -e \
        "\n[INFO] Final group totals:" \
        >> "$log"

    for i in $(seq 0 $((groups - 1))); do

        echo \
            "Group $i -> ${group_size[$i]} IPs" \
            >> "$log"

    done

    # --------------------------------------------------
    # Step 7: Return group filenames only
    # --------------------------------------------------

    echo "${outfiles[*]}" | tr ' ' '|'
}

# --------------------------------------------------
# Execute the launcher for Echo Hello probes
# --------------------------------------------------

run_udp_echo() {

    base_cmd="bash $SCRIPT_DIR/scripts/echo/echo_probing_prefixes.sh"

    result=$(balance_groups)

    IFS="|" read -r -a groups <<< "$result"

    i=0

    for group in "${groups[@]}"; do

        echo "Processing group file: $group"

        codefile_probe="$TMPDIR/echo_${i}.statuscode"

        CMD="$base_cmd $group ${SOURCE_PORTS[$i]}"
	
	    # Send the bash command, capture its exit code, signal individual tmux pane to execute

        tmux send-keys -t "${PANE_LIST[$i]}" \
            "source \"$REPO_ROOT/venv/bin/activate\" && ${CMD}; echo \$? > \"$codefile_probe\"; tmux wait-for -S done_echo_$i" C-m

        (
            tmux wait-for "done_echo_$i"

            code=$(< "$codefile_probe")

            status=$([ "$code" -eq 0 ] && echo "✅" || echo "❌")

            payload=$(printf '{"content":"%s %s : Echo protocol probe done (exit %d)"}' "$status" "$group" "$code")

            send_notification "$payload"

        ) &

        i=$((i + 1))
    done

    payload=$(printf '{"content":"ℹ️ Protocol probe started"}')

    send_notification "$payload"

    wait

    payload=$(printf '{"content":"ℹ️ Protocol probe completed"}')

    send_notification "$payload"
}

# --------------------------------------------------
# Execute the launcher for Stun probes
# --------------------------------------------------

run_stun() {
    base_cmd="bash $SCRIPT_DIR/scripts/stun/stun_probing_prefixes.sh"

    result=$(balance_groups)

    IFS="|" read -r -a groups <<< "$result"

    i=0

    echo $result
    for group in "${groups[@]}"; do

        echo "Processing group file: $group"

        codefile_probe="$TMPDIR/stun_${i}.statuscode"

        CMD="$base_cmd $group ${SOURCE_PORTS[$i]}"

	    # Send the bash command, capture its exit code, signal individual tmux pane to execute

        tmux send-keys -t "${PANE_LIST[$i]}" \
            "source \"$REPO_ROOT/venv/bin/activate\" && ${CMD}; echo \$? > \"$codefile_probe\"; tmux wait-for -S done_stun_$i" C-m

        (
            tmux wait-for "done_stun_$i"

            code=$(< "$codefile_probe")

            status=$([ "$code" -eq 0 ] && echo "✅" || echo "❌")

            payload=$(printf '{"content":"%s %s : Stun protocol probe done (exit %d)"}' "$status" "$group" "$code")

            send_notification "$payload"

        ) &

        i=$((i + 1))
    done

    payload=$(printf '{"content":"ℹ️ Protocol probe started"}')

    send_notification "$payload"

    wait

    payload=$(printf '{"content":"ℹ️ Protocol probe completed"}')

    send_notification "$payload"
}

# --------------------------------------------------
# Main execution
# --------------------------------------------------

# Fast mode

if [[ "$MODE" == "fast" ]]; then

    start=$(date +%s)

    echo -e "\n[INFO] Running protocol probing in FAST mode\n"

    if [[ "$PROTOCOL" != "stun" ]]; then
        echo "[ERROR] FAST mode currently supports only stun"
        exit 1
    fi

    if [[ ! -f "$FAST_INPUT_FILE" ]]; then
        echo "[ERROR] Missing file: $FAST_INPUT_FILE"
        exit 1
    fi

    bash "$SCRIPT_DIR/scripts/stun/stun_probing_prefixes.sh" \
        "$FAST_INPUT_FILE" \
        "42000-42010" \
        "fast"

    echo -e "\n[INFO] FAST probing completed\n"

    end=$(date +%s)

    duration=$((end - start))

    hours=$((duration / 3600))
    minutes=$(((duration % 3600) / 60))
    seconds=$((duration % 60))

    echo -e \
    "Zstun probing fast: ${hours}h ${minutes}m ${seconds}s\n" \
    >> "$TIME_LOG/summary_${PROTOCOL}_fast.log"

    # To compress results
    bash "$SCRIPT_DIR/compress.sh"

    exit 0
fi

# Full mode

start=$(date +%s)

case "$PROTOCOL" in
    echo) run_udp_echo ;;
    stun) run_stun ;;
    *) echo "Unknown protocol: $PROTOCOL"; exit 1 ;;
esac

end=$(date +%s)

duration=$((end - start))

hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))

echo -e \
"Zstun probing: ${hours}h ${minutes}m ${seconds}s\n" \
>> "$TIME_LOG/summary_${PROTOCOL}.log"

# To compress results
bash "$SCRIPT_DIR/compress.sh"
