#!/usr/bin/env python3

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PORT_SCAN_ROOT = REPO_ROOT / "port_scanning/output"
STUN_ROOT = REPO_ROOT / "zstun_probing/output"


def extract_ips(filename, expected_value):
    ips = set()

    if not filename.exists():
        return ips

    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            cols = line.split(",")

            if len(cols) < 4:
                continue

            if cols[-4].strip() == expected_value:
                ips.add(cols[0].strip())

    return ips


summary_rows = []

print("=" * 90)
print("Claim C1 Summary")
print("=" * 90)

header = (
    f"{'Country':35}"
    f"{'TCP_SYNACK':>15}"
    f"{'UDP_STUN_NO':>15}"
    f"{'STUN_YES':>15}"
)

print(header)
print("-" * len(header))

for country_dir in sorted(PORT_SCAN_ROOT.iterdir()):

    if not country_dir.is_dir():
        continue

    country = country_dir.name

    tcp_file = country_dir / "tcp_3478.txt"
    udp_file = country_dir / "udp_3478.txt"

    stun_file = (
        STUN_ROOT
        / country
        / "stun_a"
        / "stun_a.txt"
    )

    tcp_ips = extract_ips(tcp_file, "synack")
    udp_ips = extract_ips(udp_file, "stun-no")
    stun_ips = extract_ips(stun_file, "stun-yes")

    summary_rows.append([
        country,
        len(tcp_ips),
        len(udp_ips),
        len(stun_ips)
    ])

    print(
        f"{country:35}"
        f"{len(tcp_ips):15}"
        f"{len(udp_ips):15}"
        f"{len(stun_ips):15}"
    )

output_csv = REPO_ROOT / "claims/C1/c1_summary.csv"

with open(output_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Country",
        "TCP_3478",
        "UDP_3478",
        "VANILLA_STUN"
    ])
    writer.writerows(summary_rows)

print()
print(f"Summary written to: {output_csv}\n")
print("UDP_3478 < VANILLA_STUN < TCP_3478")
