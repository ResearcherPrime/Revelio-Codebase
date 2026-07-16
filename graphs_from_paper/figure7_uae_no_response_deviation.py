import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import csv
import ipaddress
from collections import defaultdict
from pathlib import Path

# --- Arguments ---
country = "United_Arab_Emirates"
SCRIPT_DIR = Path(__file__).resolve().parent
scan_folder = f"{SCRIPT_DIR}/input/dataset_2_anon"

# --- Apps ---
apps = [
    "stun_a",
    "whatsapp_a_vo", 
    "whatsapp_a_vo_randomattr",
    "messenger_a_u",
    "messenger_a_u_randomrealm",
    "telegram_a_u", 
    "signal_a_u",
]
app_labels = [
    "Vanilla_STUN", 
    "WhatsApp", 
    "Modified_WhatsApp",
    "Messenger",
    "Modified_Messenger",
    "Telegram",
    "Signal",
]

threshold = 8

# --- Paths ---
input_base = f"{scan_folder}/ip_space/{country}.txt"
output_base = f"{scan_folder}/{country}"

BAR_APPS = apps[1:]   # skip stun_a

# --- Load CIDR networks WITHOUT expansion ----
total_ips = set()

with open(input_base) as f:
    for line in f:
        line = line.strip()
        if line:
            total_ips.add(line)

print(len(total_ips))

def in_any_network(ip):
    return ip in total_ips

# ---- Collect STUN responders ----
stun_responded = set()
stun_path = f"{output_base}/{apps[0]}/{apps[0]}.txt"

if os.path.exists(stun_path):
    for chunk in pd.read_csv(stun_path, usecols=[0], names=['IP'], header=None, chunksize=100000):
        for ip in chunk['IP'].dropna():
            if in_any_network(ip):
                stun_responded.add(ip)

no_response_count = len(total_ips) - len(stun_responded)
print(no_response_count)

# Output CSV path (intermediate)
csv_out = f"{SCRIPT_DIR}/output/figure_7_{country}_per_ip_counts.csv"
os.makedirs(os.path.dirname(csv_out), exist_ok=True)

# Prepare CSV writer
csv_file = open(csv_out, "w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["IP", "UDP_Count", "ICMP_Count", "App_Variant"])

print("[*] Generating per-IP CSV ...")

for app in BAR_APPS:   # skip stun_a
    path = f"{output_base}/{app}/{app}.txt"

    if not os.path.exists(path):
        continue

    # Temporary per-app storage : ip_int -> [udp_count, icmp_count]
    ip_stats = defaultdict(lambda: [0,0])

    for chunk in pd.read_csv(
            path, usecols=[0,3,6], names=["IP","Protocol","Count"],
            header=None, chunksize=100000, on_bad_lines="skip"):

        chunk["Protocol"] = chunk["Protocol"].astype(str).str.lower().str.strip()

        for ip, proto, chunk_count in chunk.dropna().itertuples(index=False):
            cnt = int(chunk_count)

            # Skip IPs that responded to STUN
            if ip in stun_responded:
                continue

            # Skip IPs outside country prefixes
            if not in_any_network(ip):
                continue

            # Count UDP / ICMP
            if proto == "udp":
                ip_stats[ip][0] += cnt
            elif proto == "icmp":
                ip_stats[ip][1] += cnt

    # Write results to CSV
    for ip, (u_cnt, i_cnt) in ip_stats.items():
        if u_cnt == 0 and i_cnt == 0:
            continue  # skip silent IPs
        csv_writer.writerow([ip, u_cnt, i_cnt, app])

csv_file.close()
print(f"[✓] CSV saved: {csv_out}")

# -------------------------- INTERSECTIONS & PLOTTING --------------------------
print("[*] Loading per-IP counts into memory...")
df = pd.read_csv(csv_out)

udp_counts_per_app = []
icmp_counts_per_app = []
unreliable_counts_per_app = []

udp_only_ips = {app: set() for app in apps}
icmp_only_ips = {app: set() for app in apps}
unreliable_ips = {app: set() for app in apps}

# iterate over rows grouped by app to ensure each IP counted once per app (CSV already has one row per IP+app)
for ip, udp_cnt, icmp_cnt, app in df.itertuples(index=False):
    u = int(udp_cnt)
    i = int(icmp_cnt)
    if u >= threshold and i < threshold:
        udp_only_ips[app].add(ip)
    elif i >= threshold and u < threshold:
        icmp_only_ips[app].add(ip)
    elif (u + i) >= threshold:
        unreliable_ips[app].add(ip)
    # else: do not count

# Build the count arrays aligned with BAR_APPS
for app in BAR_APPS:
    udp_counts_per_app.append(len(udp_only_ips.get(app, set())))
    unreliable_counts_per_app.append(len(unreliable_ips.get(app, set())))
    icmp_counts_per_app.append(len(icmp_only_ips.get(app, set())))

# Deleting temporary file made for helping with plotting
os.remove(csv_out)

# -------------------------- PLOTTING --------------------------
scale = 0.9

x = np.arange(len(BAR_APPS)) * scale   # <-- spread bars horizontally
bar_width = 0.6   

plt.figure(figsize=(14,8), constrained_layout=False)
ax = plt.gca()

# Thick borders for academic look
border_width = 2.5
for spine in ax.spines.values():
    spine.set_linewidth(border_width)
    
plt.subplots_adjust(bottom=0.25)
# plt.yscale('log')

plt.bar(x, icmp_counts_per_app, color='#BF2B28', edgecolor='black', label=f"ICMP (≥{threshold})", width=bar_width, zorder=3)

plt.axhline(y=no_response_count, color='black', linestyle='--', linewidth=3, label="Non responsive IPs baseline")
ax.text(
    0.5, no_response_count,
    "Non responsive IPs",
    transform=ax.get_yaxis_transform(),
    ha="center", va="center",
    color="black", fontsize=20, fontweight='bold',
    bbox=dict(facecolor='white', edgecolor='none', pad=2)
)

# --- Total labels (counts) ---
totals = np.array(icmp_counts_per_app)
for i, total in enumerate(totals):
    plt.text(x[i], total, str(int(total)), ha='center', va='bottom', fontweight='bold', fontsize=20)

# --- Improved Y-axis range (log scale) ---
ymin = 10**1
ymax = max(max(totals),no_response_count,no_response_count) * 1.1
plt.ylim(ymin, ymax)

# --- Add faint vertical dotted separators (same positions as original) ---
separators = [s * scale for s in [1.5, 3.5, 4.5]]

for xpos in separators:
    plt.axvline(x=xpos, color='gray', linestyle='dashed', linewidth=1, alpha=1)

BAR_LABELS = app_labels[1:]
plt.xticks(x, [l.replace("_", "\n") for l in BAR_LABELS],  fontsize=26, fontweight='bold', rotation=-45, ha="left",rotation_mode="anchor")
for tick in plt.gca().get_xticklabels():
    tick.set_linespacing(scale)

plt.yticks(fontweight='bold', fontsize=26)
plt.ylabel("IP Count (millions)", fontsize=30, fontweight='bold')

# Legend placed OUTSIDE but does NOT shrink plot
plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), borderaxespad=0, fontsize=22, ncol=3, frameon=False, columnspacing=1.0)
plt.grid(axis='both', linestyle='-', linewidth=0.8, color='black', alpha=0.7, zorder=0)

ax.ticklabel_format(style='sci', axis='y', scilimits=(6, 6))

offset = ax.yaxis.get_offset_text()
offset.set_fontsize(0)

outpath = f"{SCRIPT_DIR}/output/figure_7_{country}_no_response_deviation.png"
plt.savefig(outpath, dpi=300)
plt.close()
print(f"[✓] Saved graph: {outpath}")
