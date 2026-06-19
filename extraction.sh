#!/usr/bin/env bash
# This code is required for extracting the input dataset shared in the `graphs_from_paper` directory.

BASE="graphs_from_paper"

echo "[*] Extracting datasets..."

for file in "$BASE/input"/*.tar.xz; do
    [ -f "$file" ] || continue

    echo "[+] Extracting $(basename "$file")"

    tar -xJf "$file" -C "$BASE/input"
done

echo "[*] Extracting output..."

tar -xJf "$BASE/output.tar.xz" -C "$BASE"

echo "[*] Done."
