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

ICMP_RESPONSE_THRESHOLD = 8

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

if len(sys.argv) != 4:

    print(
        "Usage: python3 icmp_behavior_deviation.py "
        "<country> <icmp_type> <app_config_file>"
    )

    sys.exit(1)

country = sys.argv[1]

icmp_type = int(sys.argv[2])

app_config_file = sys.argv[3]

ICMP_TYPE_LABEL = (
    "all"
    if icmp_type == -1
    else str(icmp_type)
)

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
    "icmp_deviation"
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

    icmp_types = set()

    if not os.path.exists(path):

        return udp_counts, icmp_counts, icmp_types

    for chunk in pd.read_csv(
        path,
        header=None,
        names=[
            'IP',
            'Col2',
            'Col3',
            'Protocol',
            'Type',
            'Col6',
            'Count'
        ],
        usecols=[
            'IP',
            'Protocol',
            'Count',
            'Type'
        ],
        chunksize=200000,
        on_bad_lines='skip'
    ):

        chunk['Protocol'] = (
            chunk['Protocol']
            .str.lower()
            .str.strip()
        )

        for ip, proto, cnt, itype in zip(
            chunk['IP'],
            chunk['Protocol'],
            chunk['Count'],
            chunk['Type']
        ):

            if proto == 'stun-yes' or proto == 'stun-no':

                udp_counts[ip] += cnt

            elif (
                proto == 'icmp'
                and
                (
                    itype == icmp_type
                    or
                    icmp_type == -1
                )
            ):

                icmp_counts[ip] += cnt

                icmp_types.add(itype)

    return udp_counts, icmp_counts, icmp_types

# --------------------------------------------------
# Build reference ICMP responder map
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

_, reference_icmp_counts, observed_icmp_types = (
    load_protocol_counts(reference_path)
)

print(
    f"ICMP types in {REFERENCE_APP}: "
    f"{sorted(observed_icmp_types)}"
)

reliable_reference_ips = {
    ip
    for ip, cnt in reference_icmp_counts.items()
    if cnt >= ICMP_RESPONSE_THRESHOLD
}

reliable_reference_count = len(
    reliable_reference_ips
)

unreliable_reference_ips = {
    ip
    for ip, cnt in reference_icmp_counts.items()
    if cnt < ICMP_RESPONSE_THRESHOLD
}

unreliable_reference_count = len(
    unreliable_reference_ips
)

print(
    len(reference_icmp_counts),
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

pure_udp_all = [0]

pure_icmp_all = [reliable_reference_count]

unreliable_all_udp = [0]

unreliable_all_icmp = [unreliable_reference_count]

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

    app_udp_counts, app_icmp_counts, _ = (
        load_protocol_counts(app_path)
    )

    for ip in reference_icmp_counts:

        u = app_udp_counts[ip]

        c = app_icmp_counts[ip]

        if u >= ICMP_RESPONSE_THRESHOLD:

            ips["pure_udp"].add(ip)

        elif c >= ICMP_RESPONSE_THRESHOLD:

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
        f"{app}_icmp_{ICMP_TYPE_LABEL}.txt"
    )

    with open(out_file, "w") as f:

        for category in ["pure_icmp"]:

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

    # UAE-specific ICMP type 3 logic preserved

    if icmp_type == 3:

        result = normal_ips - modified_ips

    else:

        result = modified_ips - normal_ips

    out_file = os.path.join(
        output_dir,
        f"filtered_ips_{label}.txt.icmp_{ICMP_TYPE_LABEL}"
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
    label=f'Pure UDP (≥{ICMP_RESPONSE_THRESHOLD})'
)

plt.bar(
    x,
    unreliable_all_udp,
    bottom=pure_udp_all,
    width=bar_width,
    color='#81C784',
    edgecolor='black',
    label=f'Unreliable UDP (<{ICMP_RESPONSE_THRESHOLD} packets)'
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
    label=f'Pure ICMP (≥{ICMP_RESPONSE_THRESHOLD})'
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
    label=f'Unreliable ICMP (<{ICMP_RESPONSE_THRESHOLD} packets)'
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
    "Count of Reliable ICMP-responder IPs"
)

plt.title(
    f"How {REFERENCE_APP} ICMP Responders "
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
    f"icmp_{ICMP_TYPE_LABEL}_behavior.png"
)

plt.savefig(
    outpath,
    dpi=300
)

plt.close()

print(f"[✓] Saved graph: {outpath}")
