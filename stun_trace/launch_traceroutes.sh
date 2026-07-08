#!/usr/bin/env bash

COUNTRY=$1 # United_Arab_Emirates
APP_NAME=$2 # whatsapp
DEVIATION_CATEGORY=$3 # udp, icmp, noresp

PREFIX_FILE="../scraping/prefixes/$COUNTRY.csv"
ANALYSIS_DIR="../analysis/filtered_ips/$COUNTRY"

# Select the output folder based on deviation category 
if [[ "$DEVIATION_CATEGORY" == "udp" ]]; then
    FINAL_DIFF_DIR="$ANALYSIS_DIR/udp_deviation"

elif [[ "$DEVIATION_CATEGORY" == "icmp" ]]; then
    FINAL_DIFF_DIR="$ANALYSIS_DIR/icmp_deviation"

else
    FINAL_DIFF_DIR="$ANALYSIS_DIR/no_response_deviation"

fi

# Select the diff file based on application filtered in that country
if [[ "$APP_NAME" == "whatsapp" ]]; then
    PCAP_IDX=3
    FINAL_DIFF_IPS="$FINAL_DIFF_DIR/final_diff_WhatsApp.txt"

elif [[ "$APP_NAME" == "telegram" ]]; then
    PCAP_IDX=2
    FINAL_DIFF_IPS="$FINAL_DIFF_DIR/final_diff_Telegram.txt"

elif [[ "$APP_NAME" == "signal" ]]; then
    PCAP_IDX=1
    FINAL_DIFF_IPS="$FINAL_DIFF_DIR/final_diff_Signal.txt"

elif [[ "$APP_NAME" == "messenger" ]]; then
    PCAP_IDX=0
    FINAL_DIFF_IPS="$FINAL_DIFF_DIR/final_diff_Messenger.txt"

else 
    PCAP_IDX=-1
fi

INPUT_DIR="trace_input"
PREFIX_DIR="prefixes"

mkdir -p $INPUT_DIR $PREFIX_DIR
cp "$FINAL_DIFF_IPS" "$INPUT_DIR/$COUNTRY.txt"
cp "$PREFIX_FILE" "$PREFIX_DIR/$COUNTRY.csv"

input_file="$INPUT_DIR/$COUNTRY.txt"
mkdir -p "trace_output/$COUNTRY"

while read -r line; do
    OUTPUT_FILE="trace_output/$COUNTRY/${line}_p1.txt"
    echo "Running Vanilla STUN trace for: $line"

    python3 voip_traceroute.py \
        -pcap -1 \
        -dip "$line" \
        > "$OUTPUT_FILE" 2>&1

    OUTPUT_FILE="trace_output/$COUNTRY/${line}_p2.txt"
    echo "Running VoIP app STUN trace for: $line"

    python3 voip_traceroute.py \
        -pcap "$PCAP_IDX" \
        -dip "$line" \
        > "$OUTPUT_FILE" 2>&1
done < "$input_file"
