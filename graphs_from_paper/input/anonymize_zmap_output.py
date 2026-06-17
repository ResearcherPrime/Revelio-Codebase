#!/usr/bin/env python3

import ipaddress
import random
import string
import sys

# =========================================================
# CONFIG
# =========================================================

SECRET_SEED = 12292000

# =========================================================
# CREATE PRIVATE DIGIT -> LETTER MAPPING
# =========================================================

digits = list("0123456789")

# Use 10 unique uppercase letters
letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

rng = random.Random(SECRET_SEED)
rng.shuffle(letters)

digit_map = {
    d: letters[i]
    for i, d in enumerate(digits)
}

# Example (private):
# {
#   '0': 'Q',
#   '1': 'M',
#   '2': 'A',
#   ...
# }

# =========================================================
# ANONYMIZATION FUNCTIONS
# =========================================================

def anonymize_octet(octet: int) -> str:
    # Convert octet to 3-digit string and replace each digit
    # using private digit->letter mapping.

    octet_str = f"{octet:03d}"

    return "".join(digit_map[d] for d in octet_str)


def anonymize_ip(ip: str) -> str:
    a, b, c, d = map(int, ip.strip().split("."))

    return ".".join([
        anonymize_octet(a),
        anonymize_octet(b),
        str(c),
        str(d)
    ])

# =========================================================
# MAIN CODE
# =========================================================

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <input_file> <output_file>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file) as fin, open(output_file, "w") as fout:

    for line in fin:
        line = line.strip()

        if not line:
            continue

        parts = line.split(",")

        # Anonymize first two columns if they are IPs
        for i in [0, 1]:
            try:
                parts[i] = anonymize_ip(parts[i])
            except Exception:
                pass

        fout.write(",".join(parts) + "\n")

# =========================================================
# EXAMPLE
# =========================================================

# ips = [
#     "1.2.3.4",
#     "123.45.67.89",
#     "255.255.255.255"
# ]

# for ip in ips:
#     print(ip, "->", anonymize_ip(ip))
