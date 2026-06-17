#!/usr/bin/env bash
if [[ $# -ne 3 ]] ; then
	echo 'Usage ./zmap_udp.sh country.csv sport dport'
    exit 1
fi

COUNTRY_FILE=$1
SOURCE_PORT=$2
TARGET_PORT=$3
COUNTRY="${COUNTRY_FILE%.*}"

PREFIX_DIR="./prefixes"
OUTPUT_DIR="./output/$COUNTRY"
EXEC_LOG="./logs/exec/$COUNTRY/udp_$TARGET_PORT.log"
TIME_LOG="./logs/time/$COUNTRY/udp_$TARGET_PORT.log"

# Ensure output & log folder exists
mkdir -p "$OUTPUT_DIR" "$(dirname "$EXEC_LOG")" "$(dirname "$TIME_LOG")"

input="$PREFIX_DIR/$COUNTRY_FILE"
output="$OUTPUT_DIR/udp_$TARGET_PORT.txt"

# Check if provided file argument exists
if [[ -f "$input" ]]; then

	zmap_start=$(date +%s)

	echo -e "\n[INFO] Zmap scan for udp port $TARGET_PORT started for $COUNTRY\n" | tee -a "$EXEC_LOG"
	
	# We modify zmap to store the actual src IP of the ICMP error packets recieved in the variable named outer_saddr
	# In probe-args here we use the default payload for udp probing as done in previous version of zmap, i.e., 2.1.1
	zmap -p $TARGET_PORT \
		-M udp --probe-args=hex:474554202f20485454502f312e310d0a486f73743a207777770d0a0d0a \
		-w "$input" \
		-o "$output" --output-fields=saddr,outer_saddr,success,classification,icmp_type,icmp_code \
		-s $SOURCE_PORT \
		-B 300M \
		--blocklist-file blocklist.txt 2>> "$EXEC_LOG"
	echo -e "\n[INFO] Zmap scan for udp port $TARGET_PORT completed for $COUNTRY\n" | tee -a "$EXEC_LOG"

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
