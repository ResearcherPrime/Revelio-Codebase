import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from collections import defaultdict

# --- Arguments ---
country = "United_Arab_Emirates"
scan_folder = "input/dataset_1_anon"

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
output_base = f"{scan_folder}/{country}"

# --- Step 1: Expand input IPs ---

pure_icmp_3_all = []
pure_icmp_11_all = []
unreliable_all = []
no_response_all = []

resp_map = set()
unreliable_set = set()

# --- Process remaining apps ---
for app in apps:
    nongreen = {
        "pure_icmp_3": set(),
        "pure_icmp_11": set(),
        "unreliable": set(),
        "no_response": set()
    }

    icmp_3_map = defaultdict(int)
    icmp_11_map = defaultdict(int)

    path = f"{output_base}/{app}/{app}.txt"

    if os.path.exists(path):
        for chunk in pd.read_csv(path, header=None,
            names=['IP','Col2','Col3','Protocol','Type','Col6','Count'],
            usecols=['IP','Protocol','Count','Type'], chunksize=200000, on_bad_lines='skip'):
            chunk['Protocol'] = chunk['Protocol'].str.lower().str.strip()
            for ip, proto, cnt, itype in zip(chunk['IP'], chunk['Protocol'], chunk['Count'], chunk['Type']):
                if proto == 'icmp':
                    if itype == 11:
                        icmp_11_map[ip] += cnt
                        if app == apps[0]:
                            resp_map.add(ip)
                    elif itype == 3:
                        icmp_3_map[ip] += cnt

    pure_icmp_3 = pure_icmp_11 = unreliable = no_resp = 0
    # print(len(resp_map))
    for ip in resp_map:
        u = icmp_3_map[ip]
        c = icmp_11_map[ip]
        if u >= threshold:
            pure_icmp_3 += 1
        elif c >= threshold:
            pure_icmp_11 += 1
        elif (c) > 0:
            unreliable += 1
            if  app == apps[0]:
                unreliable_set.add(ip)

    # print(pure_udp)
    pure_icmp_3_all.append(pure_icmp_3)
    pure_icmp_11_all.append(pure_icmp_11)
    unreliable_all.append(unreliable)
    no_response_all.append(no_resp)

    resp_map = resp_map - unreliable_set

# --- Plot ---
os.makedirs(f"output/icmp_deviation", exist_ok=True)

scale = 0.9
x = np.arange(len(app_labels)) * scale   # <-- spread bars horizontally
bar_width = 0.6   

plt.figure(figsize=(15,9), constrained_layout=False)
plt.subplots_adjust(bottom=0.25)

ax = plt.gca()
# Thick borders for academic look
border_width = 2.5
for spine in ax.spines.values():
    spine.set_linewidth(border_width)

# Bars
plt.bar(x, pure_icmp_11_all, width=bar_width, color='#90CAF9', edgecolor='black', zorder=3, label=f'ICMP TTL Expired (≥{threshold})')
plt.bar(x, pure_icmp_3_all, bottom=pure_icmp_11_all, width=bar_width, color='#1565C0', edgecolor='black', zorder=3, label=f'ICMP DEST Unreachable (≥{threshold})')
bottom = np.array(pure_icmp_3_all) + np.array(pure_icmp_11_all)

# Total labels at top of stacked bar (end of grey segment)
totals = bottom #np.array(pure_icmp_all)
for i, total in enumerate(totals):
    plt.text(x[i], total, str(int(total)), ha='center', va='bottom', fontweight='bold', fontsize=20)

# Small headroom so labels don’t touch plot border
plt.ylim(0, max(totals) * 1.08)

# --- Add faint vertical dotted separators ---
separators = [s * scale for s in [0.5, 2.5, 4.5, 5.5]]

for xpos in separators:
    plt.axvline(x=xpos, color='gray', linestyle='dashed', linewidth=1, alpha=1)

# X-axis labels
plt.xticks(x, [l.replace("_", "\n") for l in app_labels], fontweight='bold', fontsize=26, rotation=-45, ha="left",rotation_mode="anchor")
for tick in plt.gca().get_xticklabels():
    tick.set_linespacing(1.4)

plt.ylabel("IP Count", fontweight='bold', fontsize=30)
plt.yticks(fontweight='bold', fontsize=26)

# Legend OUTSIDE without shrinking plot
plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15),ncol=2, prop={'weight': 'bold', 'size': 22})

plt.grid(axis='both', linestyle='-', linewidth=0.8, alpha=0.8, color='black', zorder=0)

outpath = f"output/icmp_deviation/{country}_icmp_deviation_type_11.png"
plt.savefig(outpath, dpi=300)
plt.close()
print(f"[✓] Saved graph: {outpath}")
