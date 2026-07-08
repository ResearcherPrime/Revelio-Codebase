#!/usr/bin/env python3

import ipaddress
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

REPO_ROOT = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..")
)

# Shared log file
LOG_FILE = os.path.join(
    REPO_ROOT,
    "logs",
    "exec",
    "copy_prefixes.log"
)


def log_and_print(message: str):

    # Print to stdout and append to log file

    print(message)

    with open(LOG_FILE, "a") as log:
        log.write(f"{message}\n")


def merge_prefixes(prefixes):

    # Collapse overlapping or adjacent prefixes

    networks = [
        ipaddress.ip_network(p.strip())
        for p in prefixes
        if p.strip()
    ]

    collapsed = list(
        ipaddress.collapse_addresses(networks)
    )

    return collapsed


def union_ip_count(prefixes):

    # Compute exact count of unique IPs covered
    # by prefixes without full enumeration

    intervals = []

    for p in prefixes:

        net = ipaddress.ip_network(p.strip())

        start = int(net.network_address)
        end = int(net.broadcast_address)

        intervals.append((start, end))

    if not intervals:
        return 0

    intervals.sort()

    merged = []

    cur_s, cur_e = intervals[0]

    for s, e in intervals[1:]:

        if s <= cur_e + 1:

            if e > cur_e:
                cur_e = e

        else:

            merged.append((cur_s, cur_e))

            cur_s, cur_e = s, e

    merged.append((cur_s, cur_e))

    total = sum(e - s + 1 for s, e in merged)

    return total


def main():

    if len(sys.argv) != 2:

        log_and_print(
            f"Usage: {sys.argv[0]} <input_prefix_file>"
        )

        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):

        log_and_print(
            f"❌ Error: Input file '{input_file}' not found."
        )

        sys.exit(1)

    # Read prefixes

    with open(input_file, "r") as f:

        input_prefixes = [
            line.strip()
            for line in f
            if line.strip()
        ]

    # Merge prefixes

    merged = merge_prefixes(input_prefixes)

    # Sanity check using unique union count

    orig_count = union_ip_count(input_prefixes)

    merged_count = union_ip_count(
        [str(m) for m in merged]
    )

    log_and_print(
        f"Original unique IP count: {orig_count}"
    )

    log_and_print(
        f"Merged unique IP count:   {merged_count}"
    )

    if orig_count == merged_count:

        log_and_print(
            "✅ Sanity Check Passed: "
            "Merged prefixes cover the same IP space."
        )

    else:

        log_and_print(
            "❌ Sanity Check Failed: "
            "Coverage mismatch detected."
        )

    # Delete original input file

    try:

        os.remove(input_file)

    except Exception as e:

        log_and_print(
            "⚠️ Warning: "
            f"Could not delete input file "
            f"'{input_file}': {e}"
        )

    # Write merged prefixes back

    with open(input_file, "w") as f:

        for m in merged:
            f.write(str(m) + "\n")

    log_and_print(
        f"✅ Merged prefixes saved to: {input_file}"
    )


if __name__ == "__main__":

    main()

