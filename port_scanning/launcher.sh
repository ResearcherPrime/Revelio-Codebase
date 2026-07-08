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

WEBHOOK_URL=$(grep '^webhook=' "$CONFIG" | cut -d'=' -f2- | tr -d '[:space:]')     # Enter a webhook url to get updates during ongoing scraping as notifications

MODE="${1:-full}"

# Dir paths
TMPDIR="$SCRIPT_DIR/logs/temp"
PREFIXES_DIR="$SCRIPT_DIR/prefixes"
OUTPUT_DIR="$SCRIPT_DIR/output"
EXEC_LOG="$SCRIPT_DIR/logs/exec"
TIME_LOG="$SCRIPT_DIR/logs/time"
TARGET_COUNTRIES_FILE="$SCRIPT_DIR/input.csv"

start=$(date +%s)

# Commands to run in tmux
COPY_CMD=(bash $SCRIPT_DIR/copy_prefixes.sh)											# Prepare the prefixes for port scanning

# --------------------------------------------------
# Sending update notification using webhook
# --------------------------------------------------

send_notification() {

    local payload="$1"

    # If webhook URL is not configured, print the notification locally.

    if [[ -z "$WEBHOOK_URL" ]]; then
        echo -e "\n[INFO] WEBHOOK_URL is not configured."
        echo "[INFO] Enter your own webhook URL to receive notifications."
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
NUM_SESSIONS=1
declare -a PANE_LIST=()

# Read file into array
mapfile -t lines < "$TARGET_COUNTRIES_FILE"

# Check if array is empty
if [ ${#lines[@]} -eq 0 ]; then
    echo -e "\n[ERROR] File '$TARGET_COUNTRIES_FILE' is empty"
    exit 1
fi

# --------------------------------------------------
# Create tmux sessions
# --------------------------------------------------

for ((i=1; i<=NUM_SESSIONS; i++))                                                   # Splitting the tmux into individual panes to run parallel scripts
do
    # Create new tmux session

    if tmux has-session -t "port_scanning_session_$i" 2>/dev/null; then
        tmux kill-session -t "port_scanning_session_$i"
    fi

    tmux new-session -d -s "port_scanning_session_$i"
    
    # Split window into four panes in a 2x2 grid

    tmux split-window -h -t "port_scanning_session_$i:0.0"

    tmux split-window -v -t "port_scanning_session_$i:0.0"

    tmux split-window -v -t "port_scanning_session_$i:0.1"

    # Store pane IDs

    PANE_LIST+=(
        "port_scanning_session_$i:0.0"
        "port_scanning_session_$i:0.1"
        "port_scanning_session_$i:0.2"
        "port_scanning_session_$i:0.3"
    )

    # Retile panes for even 2x2 grid distribution

    tmux select-layout -t "port_scanning_session_$i:0" tiled
    
    # Select first pane

    tmux select-pane -t "port_scanning_session_$i:0.0"
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

# Run copy prefix script in the pane 0 of our tmux session
codefile="$TMPDIR/prefix_copy.code"
tmux send-keys -t "${PANE_LIST[0]}" \
  "${COPY_CMD[*]}; echo \$? > \"$codefile\"; tmux wait-for -S done_prefix_copy" C-m

# Wait for copy prefix script to finish in blocking format
tmux wait-for done_prefix_copy
code=$(< "$codefile")
status=$([ "$code" -eq 0 ] && echo "ℹ️" || echo "❌")						# Preparing the payload for status update over notification
payload=$(printf '{"content":"%s Copied the new prefixes and started zmap scans (exit %d)"}' "$status" "$code")
send_notification "$payload"

if [ "$code" -ne 0 ]; then
	echo "Pre-script failed, aborting."
	exit 1
fi

echo -e "\n[INFO] See other tmux sessions to see step by step logs\n"

j=0
# Loop through the file and select the target country prefix file
while IFS= read -r country_file; do
	country="${country_file%.*}"
	zmap_start=$(date +%s)

	echo "Processing: $country for all the required ports"	

	# Bash script to initiate zmap port scan for a single country for a fixed source and destination port
	ZMAP_CMDS=(
		"bash $SCRIPT_DIR/zmap_tcp.sh $country_file 40000-45000 3478"
		"bash $SCRIPT_DIR/zmap_udp.sh $country_file 50000-55000 3478"
	)

	WEBHOOK_MSGS=(
		"$country zmap tcp port 3478"
		"$country zmap udp port 3478"
	)

	for ((i=0; i<2; i++)); do
		# Send the bash command, capture its exit code, signal individual tmux pane to execute
		codefile="$TMPDIR/zmap_${country}_${i}.code"
		tmux send-keys -t "${PANE_LIST[$i]}" \
			"${ZMAP_CMDS[i]}; echo \$? > \"$codefile\"; tmux wait-for -S done_zmap_${country}_${i}" C-m

		# background logger → webhook
		(
			tmux wait-for done_zmap_${country}_${i}
			code=$(< "$codefile")
			status=$([ "$code" -eq 0 ] && echo "✅" || echo "❌")			    # Preparing the payload for status update over notification
			payload=$(printf '{"content":"%s %s (exit %d)"}' "$status" "${WEBHOOK_MSGS[$i]}" "$code")
			sleep $i
			send_notification "$payload"
		) &
	done

	wait # Wait for a country to complete all it's scans

    j=$((j + 1))
  
	zmap_end=$(date +%s)
	duration=$((zmap_end - zmap_start))
	hours=$((duration / 3600))
	minutes=$(((duration % 3600) / 60))
	seconds=$((duration % 60))

	echo -e "${country}: ${hours}h ${minutes}m ${seconds}s\n" >> "$TIME_LOG/total.log"

	echo "Processed: $country for all the required ports"	

	payload=$(printf '{"content":"ℹ️ %d - Zmap scans completed for %s"}' "$j" "$country")	# Preparing the payload for status update over notification
	send_notification "$payload"

done < "$TARGET_COUNTRIES_FILE"

# Log the total time spent for port scanning
echo "-------------------------" >> "$TIME_LOG/total.log"

end=$(date +%s)
duration=$((end - start))
hours=$((duration / 3600))
minutes=$(((duration % 3600) / 60))
seconds=$((duration % 60))

echo -e "\nTotal Time: ${hours}h ${minutes}m ${seconds}s\n" >> "$TIME_LOG/total.log"

# Notify that the process has completed
payload=$(printf '{"content":"ℹ️ Zmap scans completed for all the countries"}')	# Preparing the payload for status update over notification
send_notification "$payload"

# To compress results
bash "$SCRIPT_DIR/compress.sh"
