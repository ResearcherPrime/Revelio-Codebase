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

INPUT_DIR="$REPO_ROOT/scraping/prefixes"                                                  # Folder containing input CSVs with scraped data (ASN, Prefix)
OUTPUT_DIR="$SCRIPT_DIR/prefixes"                                                         # Output folder for cleaned prefix files
PYTHON_SCRIPT="$SCRIPT_DIR/merge_prefixes.py"                                             # Python script to merge overlapping prefixes
LOG_FILE="$SCRIPT_DIR/logs/exec/copy_prefixes.log"                                        # Combined log file for all execution

mkdir -p "$OUTPUT_DIR"

echo "=== Starting prefix processing and merging ==="
echo "Log file: $LOG_FILE"
echo "---------------------------------------------" >> "$LOG_FILE"

for file in "$INPUT_DIR"/*; do
    if [[ -f "$file" ]]; then
        filename=$(basename "$file")
        output_file="$OUTPUT_DIR/${filename}"

        echo "Processing: $file -> $output_file"
        echo "Processing: $file -> $output_file" >> "$LOG_FILE"

        # Step 1: Extract and clean prefixes
        tail -n +2 "$file" | cut -d',' -f2 | sed 's/^ //' > "$output_file"      # Extracting the second column from the csv file

        # Step 2: Run the Python merging script on the cleaned file
        echo "Running prefix merge on: $output_file"
        python3 "$PYTHON_SCRIPT" "$output_file" >> "$LOG_FILE" 2>&1             # Merging the prefixes 

        echo "Finished: $output_file"
        echo "---------------------------------------------" >> "$LOG_FILE"
    else
        echo "Skipping non-file: $file"
    fi
done

echo "=== Processing complete ==="
