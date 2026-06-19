#!/usr/bin/env python3

import sys
import os

# --------------------------------------------------
# Arguments
# --------------------------------------------------

if len(sys.argv) != 3:

    print(
        "Usage: python3 merge_uae_icmp_results.py "
        "<country> <app_config_file>"
    )

    sys.exit(1)

country = sys.argv[1]

app_config_file = sys.argv[2]

# --------------------------------------------------
# Paths
# --------------------------------------------------

SCRIPT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# --------------------------------------------------
# Validation
# --------------------------------------------------

if not os.path.exists(app_config_file):

    print(
        f"[ERROR] Missing config file: "
        f"{app_config_file}"
    )

    sys.exit(1)

# --------------------------------------------------
# ICMP type suffixes
# --------------------------------------------------

icmp_suffixes = [
    "icmp_11",
    "icmp_3",
    "icmp_5"
]

# --------------------------------------------------
# Filtered IP directory
# --------------------------------------------------

output_dir = os.path.join(
    SCRIPT_DIR,
    "output",
    country,
    "icmp_deviation"
)

# --------------------------------------------------
# Read app labels from config
# --------------------------------------------------

app_labels = []

with open(app_config_file, "r") as f:

    for line in f:

        line = line.strip()

        if not line or line.startswith("#"):
            continue

        packet_name, label, role, paired_app = [
            x.strip()
            for x in line.split(",")
        ]

        # Only keep normal apps
        if role == "normal":

            app_labels.append(label)

# --------------------------------------------------
# Helper
# --------------------------------------------------

def read_ips(filename):

    try:

        with open(filename, "r") as f:

            return set(
                line.strip()
                for line in f
                if line.strip()
            )

    except FileNotFoundError:

        print(f"[WARNING] Missing file: {filename}")

        return set()

# --------------------------------------------------
# Merge ICMP deviation outputs
# --------------------------------------------------

for app_label in app_labels:

    merged_ips = set()

    for suffix in icmp_suffixes:

        input_file = os.path.join(
            output_dir,
            f"filtered_ips_{app_label}.txt.{suffix}"
        )

        merged_ips |= read_ips(input_file)

    output_file = os.path.join(
        output_dir,
        f"filtered_ips_{app_label}.txt"
    )

    with open(output_file, "w") as f:

        for ip in sorted(merged_ips):

            f.write(ip + "\n")

    print(
        f"[✓] Written {len(merged_ips)} IPs to "
        f"{output_file}"
    )
