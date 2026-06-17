#!/usr/bin/env python3

import random
import sys

# =========================================================
# CONFIG
# =========================================================

SECRET_SEED = 12292000

# =========================================================
# PRIVATE DIGIT -> LETTER MAPPING
# =========================================================

digits = list("0123456789")

letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

rng = random.Random(SECRET_SEED)
rng.shuffle(letters)

digit_map = {
    d: letters[i]
    for i, d in enumerate(digits)
}

# =========================================================
# ANONYMIZATION FUNCTIONS
# =========================================================

def anonymize_octet(octet: int) -> str:
    octet_str = f"{octet:03d}"
    return "".join(digit_map[d] for d in octet_str)


def anonymize_ip(ip: str) -> str:
    a, b, c, d = map(int, ip.strip().split("."))

    # Only anonymize first two octets
    return ".".join([
        anonymize_octet(a),
        anonymize_octet(b),
        str(c),
        str(d)
    ])


# =========================================================
# MAIN
# =========================================================

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <input_file> <output_file>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file) as fin, open(output_file, "w") as fout:

    for line in fin:

        line = line.strip()

        # Ignore blanks
        if not line:
            continue

        # Ignore comments
        if line.startswith("#"):
            continue

        try:
            anon_ip = anonymize_ip(line)
            fout.write(anon_ip + "\n")

        except Exception:
            print(f"Skipping invalid IP: {line}", file=sys.stderr)
