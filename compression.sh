#!/usr/bin/env bash

BASE="graphs_from_paper"

echo "[*] Compressing datasets..."

for dir in "$BASE/input"/*/; do
    [ -d "$dir" ] || continue

    name=$(basename "$dir")

    echo "[+] Compressing $name"

    tar -cf - -C "$BASE/input" "$name" | \
        xz -9e -T0 > "$BASE/input/${name}.tar.xz"

    rm -rf "$dir"
done

echo "[*] Compressing output folder..."

tar -cf - -C "$BASE" output | \
    xz -9e -T0 > "$BASE/output.tar.xz"

rm -rf "$BASE/output"

echo "[*] Done."
