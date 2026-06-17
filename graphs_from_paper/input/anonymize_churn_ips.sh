#!/usr/bin/env bash

INPUT_BASE="dataset_3"
OUTPUT_BASE=${INPUT_BASE}_anon

SCRIPT="anonymize_churn_ips.py"

mkdir -p "$OUTPUT_BASE"

find "$INPUT_BASE" -type f -name "*.txt" | while read -r infile; do

    # Relative path from input base
    relpath="${infile#$INPUT_BASE/}"

    # Output file path
    outfile="$OUTPUT_BASE/$relpath"

    # Create corresponding output directory
    outdir=$(dirname "$outfile")
    mkdir -p "$outdir"

    echo "Processing: $infile"

    python3 "$SCRIPT" "$infile" "$outfile"

done
