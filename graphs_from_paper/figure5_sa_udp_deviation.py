import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from collections import defaultdict

# --- Arguments ---
country = "Saudi_Arabia"
scan_folder = "input/dataset_2_anon"

# --- Apps & Labels (As requested) ---
apps = [
    "stun_a",
    "telegram_a_u", 
    "telegram_a_u_randomrealm", 
    "whatsapp_a_vo", 
    "messenger_a_u",
    "signal_a_u", 
]

app_labels = [
    "Vanilla_STUN",
    "Telegram", 
    "Telegram_Modified",  
    "WhatsApp", 
    "Messenger",
    "Signal",
]

threshold = 8

# --- Paths ---
output_base = f"{scan_folder}/{country}"

# --- Build STUN baseline ---
udp_counts = defaultdict(int)
path = f"{output_base}/{apps[0]}/{apps[0]}.txt"

if os.path.exists(path):
    for chunk in pd.read_csv(path, header=None,
        names=['IP','Col2','Col3','Protocol','Col5','Col6','Count'],
        usecols=['IP','Protocol','Count'], chunksize=200000, on_bad_lines='skip'):
        chunk['Protocol'] = chunk['Protocol'].str.lower().str.strip()
        for ip, proto, cnt in zip(chunk['IP'], chunk['Protocol'], chunk['Count']):
            if proto == 'udp':
                udp_counts[ip] += cnt

baseline_udp_ips = {ip for ip, cnt in udp_counts.items() if cnt >= threshold}
baseline_count = len(baseline_udp_ips)
unreliable_ips = {ip for ip, cnt in udp_counts.items() if cnt < threshold}
unreliable_count = len(unreliable_ips)
print(len(udp_counts), len(baseline_udp_ips), len(unreliable_ips))

pure_udp_all = [baseline_count]
pure_icmp_all = [0]
unreliable_all_udp = [0] # Keeping it zero because we only want to see IPs which gave >8 responses for baseline
unreliable_all_icmp = [0]
no_response_all = [0]

# --- Process remaining apps ---
for app in apps[1:]:
    nongreen = {
        "pure_icmp": set(),
        "unreliable_udp": set(),
        "unreliable_icmp": set(),
        "no_response": set()
    }

    udp_map = defaultdict(int)
    icmp_map = defaultdict(int)
    path = f"{output_base}/{app}/{app}.txt"

    if os.path.exists(path):
        for chunk in pd.read_csv(path, header=None,
            names=['IP','Col2','Col3','Protocol','Col5','Col6','Count'],
            usecols=['IP','Protocol','Count'], chunksize=200000, on_bad_lines='skip'):
            chunk['Protocol'] = chunk['Protocol'].str.lower().str.strip()
            for ip, proto, cnt in zip(chunk['IP'], chunk['Protocol'], chunk['Count']):
                if proto == 'udp':
                    udp_map[ip] += cnt
                elif proto == 'icmp':
                    icmp_map[ip] += cnt

    pure_udp = pure_icmp = unreliable_udp = unreliable_icmp = no_resp = 0

    for ip in baseline_udp_ips:
        u = udp_map[ip]
        c = icmp_map[ip]
        if u >= threshold:
            pure_udp += 1
        elif c >= threshold:
            pure_icmp += 1
        elif (u) > 0:
            unreliable_udp += 1
        elif (c) > 0:
            unreliable_icmp += 1
        else:
            no_resp += 1

    pure_udp_all.append(pure_udp)
    pure_icmp_all.append(pure_icmp)
    unreliable_all_udp.append(unreliable_udp)
    unreliable_all_icmp.append(unreliable_icmp)
    no_response_all.append(no_resp)

# --- 2. VISUALIZATION ---
os.makedirs("output/udp_deviation", exist_ok=True)

print("Pure UDP:", pure_udp_all)
print("Pure ICMP:", pure_icmp_all)
print("Unreliable UDP:", unreliable_all_udp)
print("No Response", no_response_all)

# Spacing settings
scale = 1.2  
x = np.arange(len(app_labels)) * scale
bar_width = 0.6 

plt.figure(figsize=(14, 8))
ax = plt.gca()

# Thick borders for academic look
border_width = 2.5
for spine in ax.spines.values():
    spine.set_linewidth(border_width)

# Stacked Bar Logic
# 1. Pure UDP
plt.bar(x, pure_udp_all, width=bar_width, color='#2E7D32', zorder=3, 
        edgecolor='black', linewidth=1.5, label=f'UDP (≥{threshold})')

# 2. Unreliable
plt.bar(x, unreliable_all_udp, bottom=pure_udp_all, width=bar_width, zorder=3, 
        color='#81C784', edgecolor='black', linewidth=1.5, label='Throttled UDP')

# 3. Pure ICMP 
bottom_unrel = np.array(pure_udp_all) + np.array(unreliable_all_udp)
plt.bar(x, pure_icmp_all, bottom=bottom_unrel, width=bar_width, zorder=3, alpha=0.9,
        color='#1565C0', edgecolor='black', linewidth=1.5, label=f'ICMP (≥{threshold})')

# 4. No Response (The Dashed Box)
bottom_noresp = bottom_unrel + np.array(pure_icmp_all)
plt.bar(x, no_response_all, bottom=bottom_noresp, width=bar_width, zorder=3, 
        color='#eeeeee', edgecolor='black', linewidth=1.5, linestyle='--', label='No Response')

# --- 3. LABELS AND ANNOTATIONS ---
# Total labels on top of the bars
# totals = bottom_noresp + np.array(no_response_all)
for i, total in enumerate(bottom_noresp):
    plt.text(x[i], total + (max(bottom_noresp) * 0.01), str(int(total)),
             ha='center', va='bottom', fontweight='bold', fontsize=20)

plt.ylim(0, max(bottom_noresp) * 1.15)

# Group separators
separators = [s * scale for s in [0.5, 2.5, 3.5, 4.5]]
for xpos in separators:
    plt.axvline(x=xpos, color='gray', linestyle='dashed', linewidth=1, alpha=0.4)

# Axis formatting
plt.xticks(x, [l.replace("_", "\n") for l in app_labels], fontweight='bold', fontsize=26, rotation=-45, ha='right')
plt.yticks(fontweight='bold', fontsize=26)
plt.ylabel("IP Count", fontweight='bold', fontsize=30)
# plt.xlabel(f"UDP Deviation Analysis - {country}", fontweight='bold', fontsize=30)

# Legend outside
plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), borderaxespad=0, fontsize=22, ncol=4, frameon=True, columnspacing=1.0, framealpha=0.9)
plt.grid(axis='both', linestyle='-',linewidth=0.8, alpha=0.8, color='black', zorder=0)

# --- 4. EXPORT ---
plt.tight_layout()
outpath = f"output/udp_deviation/{country}_udp_deviation.png"
plt.savefig(outpath, dpi=600)
plt.close()

print(f"[✓] Graph created successfully: {outpath}")
