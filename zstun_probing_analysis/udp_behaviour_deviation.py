#!/usr/bin/env python3

import matplotlib
matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

from collections import defaultdict

# --------------------------------------------------
# Constants
# --------------------------------------------------

UDP_RESPONSE_THRESHOLD = 8

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
        "Usage: python3 udp_behavior_deviation.py "
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
# Paths
# --------------------------------------------------

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
    "udp_deviation"
)

graph_dir = os.path.join(
    output_dir,
    "graphs"
)

os.makedirs(output_dir, exist_ok=True)

os.makedirs(graph_dir, exist_ok=True)

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
        header=None,
        names=[
            'IP',
            'Col2',
            'Col3',
            'Protocol',
            'Col5',
            'Col6',
            'Count'
        ],
        usecols=['IP', 'Protocol', 'Count'],
        chunksize=200000,
        on_bad_lines='skip'
    ):

        chunk['Protocol'] = (
            chunk['Protocol']
            .str.lower()
            .str.strip()
        )

        for ip, proto, cnt in zip(
            chunk['IP'],
            chunk['Protocol'],
            chunk['Count']
        ):

            if proto == 'stun-yes':
                udp_counts[ip] += cnt

            elif proto == 'stun-no':
                # Although the udp packets are not stun packets but if the deviation
                # exists along the path to these IPs then we need to condider them filtered
                udp_counts[ip] += cnt                

            elif proto == 'icmp':
                icmp_counts[ip] += cnt

    return udp_counts, icmp_counts

# --------------------------------------------------
# Build reference UDP responder map
# --------------------------------------------------

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

reference_udp_counts, _ = load_protocol_counts(
    reference_path
)

reliable_reference_ips = {
    ip
    for ip, cnt in reference_udp_counts.items()
    if cnt >= UDP_RESPONSE_THRESHOLD
}

reliable_reference_count = len(
    reliable_reference_ips
)

unreliable_reference_ips = {
    ip
    for ip, cnt in reference_udp_counts.items()
    if cnt < UDP_RESPONSE_THRESHOLD
}

unreliable_reference_count = len(
    unreliable_reference_ips
)

print(
    len(reference_udp_counts),
    reliable_reference_count,
    unreliable_reference_count
)

# --------------------------------------------------
# Write reliable reference IPs
# --------------------------------------------------

reference_output = os.path.join(
    output_dir,
    f"{REFERENCE_APP}.txt"
)

with open(reference_output, "w") as f:

    for ip in sorted(reliable_reference_ips):
        f.write(ip + "\n")

print(
    f"[✓] Saved {reliable_reference_count} "
    f"{REFERENCE_APP} IPs to "
    f"{reference_output}"
)

# --------------------------------------------------
# Plot accumulators
# --------------------------------------------------

pure_udp_all = [reliable_reference_count]

pure_icmp_all = [0]

unreliable_all_udp = [unreliable_reference_count]

unreliable_all_icmp = [0]

no_response_all = [0]

# --------------------------------------------------
# Process remaining apps
# --------------------------------------------------

for app in apps[1:]:

    ips = {
        "pure_udp": set(),
        "pure_icmp": set(),
        "unreliable_udp": set(),
        "unreliable_icmp": set(),
        "no_response": set()
    }

    app_path = os.path.join(
        output_base,
        app,
        f"{app}.txt"
    )

    app_udp_counts, app_icmp_counts = (
        load_protocol_counts(app_path)
    )

    for ip in reference_udp_counts:

        u = app_udp_counts[ip]

        c = app_icmp_counts[ip]

        if u >= UDP_RESPONSE_THRESHOLD:

            ips["pure_udp"].add(ip)

        elif c >= UDP_RESPONSE_THRESHOLD:

            ips["pure_icmp"].add(ip)

        elif u > 0:

            ips["unreliable_udp"].add(ip)

        elif c > 0:

            ips["unreliable_icmp"].add(ip)

        else:

            ips["no_response"].add(ip)

    pure_udp_all.append(
        len(ips["pure_udp"])
    )

    pure_icmp_all.append(
        len(ips["pure_icmp"])
    )

    unreliable_all_udp.append(
        len(ips["unreliable_udp"])
    )

    unreliable_all_icmp.append(
        len(ips["unreliable_icmp"])
    )

    no_response_all.append(
        len(ips["no_response"])
    )

    # --------------------------------------------------
    # Write output IPs
    # --------------------------------------------------

    out_file = os.path.join(
        output_dir,
        f"{app}.txt"
    )

    with open(out_file, "w") as f:

        for category in [
            "pure_udp",
            "unreliable_udp"
        ]:

            f.write(category + "\n")

            for ip in sorted(ips[category]):
                f.write(ip + "\n")

            f.write("\n")

# --------------------------------------------------
# Modified vs normal comparison
# --------------------------------------------------

for normal_app, modified_app, label in MODIFIED_APP_PAIRS:

    modified_file = os.path.join(
        output_dir,
        f"{modified_app}.txt"
    )

    normal_file = os.path.join(
        output_dir,
        f"{normal_app}.txt"
    )

    if (
        not os.path.exists(modified_file)
        or
        not os.path.exists(normal_file)
    ):
        continue

    modified_ips = read_ips(modified_file)

    normal_ips = read_ips(normal_file)

    result = modified_ips - normal_ips

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

x = np.arange(len(app_labels)) * 1.35

bar_width = 0.75

plt.figure(
    figsize=(18, 6),
    constrained_layout=False
)

plt.subplots_adjust(bottom=0.25)

# --------------------------------------------------
# Bars
# --------------------------------------------------

plt.bar(
    x,
    pure_udp_all,
    width=bar_width,
    color='#2E7D32',
    edgecolor='black',
    label=f'Pure UDP (≥{UDP_RESPONSE_THRESHOLD})'
)

plt.bar(
    x,
    unreliable_all_udp,
    bottom=pure_udp_all,
    width=bar_width,
    color='#81C784',
    edgecolor='black',
    label=f'Unreliable UDP (<{UDP_RESPONSE_THRESHOLD} packets)'
)

bottom_pure_icmp = (
    np.array(pure_udp_all)
    +
    np.array(unreliable_all_udp)
)

plt.bar(
    x,
    pure_icmp_all,
    bottom=bottom_pure_icmp,
    width=bar_width,
    color='#1565C0',
    edgecolor='black',
    label=f'Pure ICMP (≥{UDP_RESPONSE_THRESHOLD})'
)

bottom_unrel_icmp = (
    bottom_pure_icmp
    +
    np.array(pure_icmp_all)
)

plt.bar(
    x,
    unreliable_all_icmp,
    bottom=bottom_unrel_icmp,
    width=bar_width,
    color='#90CAF9',
    edgecolor='black',
    label=f'Unreliable ICMP (<{UDP_RESPONSE_THRESHOLD} packets)'
)

bottom_noresp = (
    bottom_unrel_icmp
    +
    np.array(unreliable_all_icmp)
)

plt.bar(
    x,
    no_response_all,
    bottom=bottom_noresp,
    width=bar_width,
    color='#AAAAAA',
    edgecolor='black',
    label='No Response'
)

# --------------------------------------------------
# Labels
# --------------------------------------------------

totals = bottom_noresp

for i, total in enumerate(totals):

    plt.text(
        x[i],
        total,
        str(int(total)),
        ha='center',
        va='bottom',
        fontweight='bold'
    )

plt.ylim(0, max(totals) * 1.08)

# --------------------------------------------------
# X-axis
# --------------------------------------------------

plt.xticks(
    x,
    [l.replace("_", "\n") for l in app_labels],
    rotation=25,
    ha="right"
)

for tick in plt.gca().get_xticklabels():
    tick.set_linespacing(1.4)

# --------------------------------------------------
# Labels & title
# --------------------------------------------------

plt.ylabel(
    "Count of Reliable UDP-responder IPs"
)

plt.title(
    f"How {REFERENCE_APP} UDP Responders "
    f"Behave for Other Apps — {country}"
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
    "udp_behavior.png"
)

plt.savefig(
    outpath,
    dpi=300
)

plt.close()

print(f"[✓] Saved graph: {outpath}")
