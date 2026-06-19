#!/usr/bin/env python3

import matplotlib
matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import ipaddress

from collections import defaultdict

# --------------------------------------------------
# Constants
# --------------------------------------------------

RESPONSE_THRESHOLD = 8

ICMP_TYPE = -1

ICMP_TYPE_LABEL = (
    "all"
    if ICMP_TYPE == -1
    else str(ICMP_TYPE)
)

# --------------------------------------------------
# Paths
# --------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

REPO_ROOT = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..")
)

# --------------------------------------------------
# Arguments
# --------------------------------------------------

if len(sys.argv) != 3:

    print(
        "Usage: python3 no_response_behavior_deviation.py "
        "<country> <app_config_file>"
    )

    sys.exit(1)

country = sys.argv[1]

app_config_file = sys.argv[2]

# --------------------------------------------------
# Validation
# --------------------------------------------------

if not os.path.exists(app_config_file):

    print(f"[ERROR] Missing config file: {app_config_file}")

    sys.exit(1)

# --------------------------------------------------
# App configuration
# --------------------------------------------------

APP_CONFIGS = []

REFERENCE_APP = None

MODIFIED_APP_PAIRS = []

with open(app_config_file, "r") as f:

    for line in f:

        line = line.strip()

        if not line or line.startswith("#"):
            continue

        packet_name, label, role, paired_app = [
            x.strip() for x in line.split(",")
        ]

        APP_CONFIGS.append(
            (packet_name, label, role, paired_app)
        )

        if role == "baseline":
            REFERENCE_APP = packet_name

        if role == "normal" and paired_app:

            MODIFIED_APP_PAIRS.append(
                (
                    packet_name,
                    paired_app,
                    label
                )
            )

if REFERENCE_APP is None:

    print("[ERROR] No reference app configured")

    sys.exit(1)

apps = [x[0] for x in APP_CONFIGS]

app_labels = [x[1] for x in APP_CONFIGS]

BAR_APPS = apps[1:]

BAR_LABELS = app_labels[1:]

# --------------------------------------------------
# Paths
# --------------------------------------------------

input_base = os.path.join(
    REPO_ROOT,
    "zstun_probing",
    "prefixes",
    f"{country}.txt"
)

output_base = os.path.join(
    REPO_ROOT,
    "zstun_probing",
    "output",
    country
)

output_dir = os.path.join(
    SCRIPT_DIR,
    "output",
    country,
    "no_response_deviation"
)

graph_dir = os.path.join(
    output_dir,
    "graphs"
)

os.makedirs(output_dir, exist_ok=True)

os.makedirs(graph_dir, exist_ok=True)

# --------------------------------------------------
# Load country prefixes
# --------------------------------------------------

ip_ranges = []

if os.path.exists(input_base):

    with open(input_base) as f:

        for line in f:

            if line.strip():

                net = ipaddress.ip_network(
                    line.strip(),
                    strict=False
                )

                ip_ranges.append(
                    (
                        int(net.network_address),
                        int(net.broadcast_address)
                    )
                )

else:

    print(
        f"[ERROR] Missing prefix file: "
        f"{input_base}"
    )

    sys.exit(1)

ip_ranges.sort()

# --------------------------------------------------
# Binary-search prefix membership
# --------------------------------------------------

def in_any_network(ip):

    ip_int = int(ipaddress.ip_address(ip))

    left, right = 0, len(ip_ranges) - 1

    while left <= right:

        mid = (left + right) // 2

        start, end = ip_ranges[mid]

        if start <= ip_int <= end:
            return True

        elif ip_int < start:
            right = mid - 1

        else:
            left = mid + 1

    return False

# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def read_ips(filename):

    with open(filename, "r") as f:

        return set(
            line.strip()
            for line in f
            if line.strip()
        )

def load_protocol_counts(path):

    udp_counts = defaultdict(int)

    icmp_counts = defaultdict(int)

    if not os.path.exists(path):

        return udp_counts, icmp_counts

    for chunk in pd.read_csv(
        path,
        usecols=[0,3,4,6],
        names=["IP","Protocol","Type","Count"],
        header=None,
        chunksize=100000,
        on_bad_lines="skip"
    ):

        chunk["Protocol"] = (
            chunk["Protocol"]
            .astype(str)
            .str.lower()
            .str.strip()
        )

        for ip, proto, itype, chunk_count in (
            chunk.dropna().itertuples(index=False)
        ):

            cnt = int(chunk_count)

            if proto == "stun-yes" or proto == "stun-no":

                udp_counts[ip] += cnt

            elif (
                proto == "icmp"
                and
                (
                    itype == ICMP_TYPE
                    or
                    ICMP_TYPE == -1
                )
            ):

                icmp_counts[ip] += cnt

    return udp_counts, icmp_counts

# --------------------------------------------------
# Collect reference responders
# --------------------------------------------------

reference_responded_ips = set()

reference_path = os.path.join(
    output_base,
    REFERENCE_APP,
    f"{REFERENCE_APP}.txt"
)

if not os.path.exists(reference_path):

    print(
        f"[ERROR] Missing reference file: "
        f"{reference_path}"
    )

    sys.exit(1)

for chunk in pd.read_csv(
    reference_path,
    usecols=[0],
    names=['IP'],
    header=None,
    chunksize=100000
):

    for ip in chunk['IP'].dropna():

        if in_any_network(ip):

            reference_responded_ips.add(
                int(ipaddress.ip_address(ip))
            )

# --------------------------------------------------
# Reference no-response population
# --------------------------------------------------

total_ips = sum(
    (end - start + 1)
    for start, end in ip_ranges
)

reference_no_response_count = (
    total_ips - len(reference_responded_ips)
)

# --------------------------------------------------
# Per-app accumulators
# --------------------------------------------------

udp_counts_per_app = []

icmp_counts_per_app = []

unreliable_udp_counts_per_app = []

unreliable_icmp_counts_per_app = []

# --------------------------------------------------
# Process apps
# --------------------------------------------------

for app in BAR_APPS:

    ips = {
        "pure_udp": set(),
        "pure_icmp": set(),
        "unreliable_udp": set(),
        "unreliable_icmp": set(),
    }

    path = os.path.join(
        output_base,
        app,
        f"{app}.txt"
    )

    app_udp_counts, app_icmp_counts = (
        load_protocol_counts(path)
    )

    for ip in set(
        list(app_udp_counts.keys())
        +
        list(app_icmp_counts.keys())
    ):

        ip_int = int(ipaddress.ip_address(ip))

        # Skip reference responders

        if ip_int in reference_responded_ips:
            continue

        # Skip IPs outside country

        if not in_any_network(ip):
            continue

        u = app_udp_counts[ip]

        i = app_icmp_counts[ip]

        if u >= RESPONSE_THRESHOLD:

            ips["pure_udp"].add(ip)

        elif i >= RESPONSE_THRESHOLD:

            ips["pure_icmp"].add(ip)

        elif u > 0:

            ips["unreliable_udp"].add(ip)

        elif i > 0:

            ips["unreliable_icmp"].add(ip)

    # --------------------------------------------------
    # Save filtered IPs
    # --------------------------------------------------

    out_file = os.path.join(
        output_dir,
        f"{app}_icmp_{ICMP_TYPE_LABEL}.txt"
    )

    with open(out_file, "w") as f:

        for category in ["pure_icmp"]:

            f.write(category + "\n")

            for ip in sorted(ips[category]):
                f.write(ip + "\n")

            f.write("\n")

    # --------------------------------------------------
    # Graph accumulators
    # --------------------------------------------------

    udp_counts_per_app.append(
        len(ips["pure_udp"])
    )

    unreliable_udp_counts_per_app.append(
        len(ips["unreliable_udp"])
    )

    unreliable_icmp_counts_per_app.append(
        len(ips["unreliable_icmp"])
    )

    icmp_counts_per_app.append(
        len(ips["pure_icmp"])
    )

# --------------------------------------------------
# Modified vs normal comparison
# --------------------------------------------------

for normal_app, modified_app, label in MODIFIED_APP_PAIRS:

    modified_file = os.path.join(
        output_dir,
        f"{modified_app}_icmp_{ICMP_TYPE_LABEL}.txt"
    )

    normal_file = os.path.join(
        output_dir,
        f"{normal_app}_icmp_{ICMP_TYPE_LABEL}.txt"
    )

    if (
        not os.path.exists(modified_file)
        or
        not os.path.exists(normal_file)
    ):
        continue

    modified_ips = read_ips(modified_file)

    normal_ips = read_ips(normal_file)

    # Preserve original semantics:
    # normal minus modified

    result = normal_ips - modified_ips

    out_file = os.path.join(
        output_dir,
        f"filtered_ips_{label}.txt"
    )

    with open(out_file, "w") as f:

        for ip in sorted(result):
            f.write(ip + "\n")

# --------------------------------------------------
# Plot
# --------------------------------------------------

x = np.arange(len(BAR_APPS)) * 1.35

plt.figure(
    figsize=(18,6),
    constrained_layout=False
)

plt.subplots_adjust(bottom=0.25)

plt.yscale('log')

# --------------------------------------------------
# Bars
# --------------------------------------------------

plt.bar(
    x,
    udp_counts_per_app,
    color='#2E7D32',
    edgecolor='black',
    label=f"UDP-only (≥{RESPONSE_THRESHOLD})",
    width=0.75
)

plt.bar(
    x,
    unreliable_udp_counts_per_app,
    bottom=np.array(udp_counts_per_app),
    color='#81C784',
    edgecolor='black',
    label="Unreliable UDP",
    width=0.75
)

bottom_icmp = (
    np.array(udp_counts_per_app)
    +
    np.array(unreliable_udp_counts_per_app)
)

plt.bar(
    x,
    icmp_counts_per_app,
    bottom=bottom_icmp,
    color='#1565C0',
    edgecolor='black',
    label=f"ICMP-only (≥{RESPONSE_THRESHOLD})",
    width=0.75
)

bottom_unrel_icmp = (
    bottom_icmp
    +
    np.array(icmp_counts_per_app)
)

plt.bar(
    x,
    unreliable_icmp_counts_per_app,
    bottom=bottom_unrel_icmp,
    color='#90CAF9',
    edgecolor='black',
    label="Unreliable ICMP",
    width=0.75
)

# --------------------------------------------------
# Reference no-response baseline
# --------------------------------------------------

plt.axhline(
    y=reference_no_response_count,
    color='red',
    linestyle='--',
    linewidth=2,
    label="Reference STUN no-response baseline"
)

# --------------------------------------------------
# Labels
# --------------------------------------------------

totals = (
    bottom_icmp
    +
    np.array(icmp_counts_per_app)
)

for i, total in enumerate(totals):

    plt.text(
        x[i],
        total,
        str(int(total)),
        ha='center',
        va='bottom',
        fontweight='bold',
        fontsize=10
    )

# --------------------------------------------------
# Y-axis
# --------------------------------------------------

ymin = 10**1

ymax = (
    10 ** (
        np.ceil(
            np.log10(
                max(reference_no_response_count, 10)
            )
        )
    )
) * 1.10

plt.ylim(ymin, ymax)

# --------------------------------------------------
# X-axis
# --------------------------------------------------

plt.xticks(
    x,
    [l.replace("_", "\n") for l in BAR_LABELS],
    rotation=25,
    ha="right"
)

for tick in plt.gca().get_xticklabels():
    tick.set_linespacing(1.4)

# --------------------------------------------------
# Labels & title
# --------------------------------------------------

plt.ylabel("Reliable Responder IP Count")

plt.title(
    f"IPs that responded nothing to "
    f"{REFERENCE_APP} but something to "
    f"VoIP app STUN — {country}"
)

# --------------------------------------------------
# Legend & grid
# --------------------------------------------------

plt.legend(
    loc='upper left',
    bbox_to_anchor=(1.02, 1),
    borderaxespad=0
)

plt.grid(
    axis='y',
    linestyle='--',
    alpha=0.5
)

# --------------------------------------------------
# Save graph
# --------------------------------------------------

outpath = os.path.join(
    graph_dir,
    f"no_response_behavior_icmp_{ICMP_TYPE_LABEL}.png"
)

plt.savefig(
    outpath,
    dpi=300
)

plt.close()

print(f"[✓] Saved graph: {outpath}")
