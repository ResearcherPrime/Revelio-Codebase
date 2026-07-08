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
# Dir paths
# --------------------------------------------------

if [[ $# -ne 3 ]] ; then
	echo 'Usage ./zmap_tcp.sh country.csv sport dport'
    exit 1
fi

COUNTRY_FILE=$1
SOURCE_PORT=$2
TARGET_PORT=$3
COUNTRY="${COUNTRY_FILE%.*}"
NUM_PROBES=10

PREFIX_DIR="$SCRIPT_DIR/prefixes"
OUTPUT_DIR="$SCRIPT_DIR/output/$COUNTRY"
EXEC_LOG="$SCRIPT_DIR/logs/exec/$COUNTRY/tcp_$TARGET_PORT.log"
TIME_LOG="$SCRIPT_DIR/logs/time/$COUNTRY/tcp_$TARGET_PORT.log"

# Ensure output & log folder exists
mkdir -p "$OUTPUT_DIR" "$(dirname "$EXEC_LOG")" "$(dirname "$TIME_LOG")"

input="$PREFIX_DIR/$COUNTRY_FILE"
output="$OUTPUT_DIR/tcp_$TARGET_PORT.txt"

# Check if provided file argument exists
if [[ -f "$input" ]]; then

	zmap_start=$(date +%s)

	echo -e "\n[INFO] Zmap scan for tcp port $TARGET_PORT started for $COUNTRY\n" | tee -a "$EXEC_LOG"
	
	# We modify zmap to store the actual src IP of the ICMP error packets recieved in the variable named outer_saddr
	zmap -p $TARGET_PORT \
		-M tcp_synscan \
		-w "$input" \
		-o "$output" --output-fields=saddr,outer_saddr,success,classification,icmp_type,icmp_code \
		-s $SOURCE_PORT \
		-B 300M \
        --probes "$NUM_PROBES" \
		--blocklist-file $SCRIPT_DIR/blocklist.txt 2>> "$EXEC_LOG" 
	echo -e "\n[INFO] Zmap scan for tcp port $TARGET_PORT completed for $COUNTRY\n" | tee -a "$EXEC_LOG"

	zmap_end=$(date +%s)
	duration=$((zmap_end - zmap_start))
	hours=$((duration / 3600))
	minutes=$(((duration % 3600) / 60))
	seconds=$((duration % 60))

	echo -e "\n[INFO] ${hours}h ${minutes}m ${seconds}s\n" | tee -a "$TIME_LOG"
else
	echo -e "File not found!" | tee -a "$EXEC_LOG"
	exit 1
fi

exit 0
