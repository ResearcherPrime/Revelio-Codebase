#!/usr/bin/env python3

import ipaddress
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
    a, b, c, d = map(int, str(ip).split("."))

    # Only anonymize first 2 octets
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
    print(f"Usage: {sys.argv[0]} <prefix_file> <output_file>")
    sys.exit(1)

prefix_file = sys.argv[1]
output_file = sys.argv[2]

unique_ips = set()

with open(prefix_file) as f:

    for line in f:

        line = line.strip()

        # Ignore blanks/comments
        if not line or line.startswith("#"):
            continue

        try:
            net = ipaddress.ip_network(line, strict=False)

            # Enumerate all usable hosts
            for ip in net.hosts():

                anon_ip = anonymize_ip(ip)

                unique_ips.add(anon_ip)

        except Exception:
            print(f"Skipping invalid prefix: {line}")

# =========================================================
# WRITE OUTPUT
# =========================================================

with open(output_file, "w") as out:

    for ip in sorted(unique_ips):
        out.write(ip + "\n")

print(f"Total unique anonymized IPs: {len(unique_ips)}")
