import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --- 1. Settings & Targets ---
TARGET_COUNTRIES = [
    "Azerbaijan", "Estonia", "Iraq", "Kazakhstan", "Kyrgyzstan", 
    "Mexico", "Myanmar", "Qatar", "South_Africa", 
    "Egypt", "Indonesia", "Jordan", "Kuwait", "Malaysia", 
    "Morocco", "Pakistan", "Turkey", "Saudi_Arabia", "United_Arab_Emirates"
]

COUNTRY_CODES = {
    "Azerbaijan": "AZ", "Estonia": "EE", "Iraq": "IQ", "Kazakhstan": "KZ",
    "Kyrgyzstan": "KG", "Mexico": "MX", "Myanmar": "MM", "Qatar": "QA",
    "South_Africa": "ZA", "Egypt": "EG", "Indonesia": "ID", "Jordan": "JO",
    "Kuwait": "KW", "Malaysia": "MY", "Morocco": "MA", "Pakistan": "PK",
    "Saudi_Arabia": "SA", "Turkey": "TR", "United_Arab_Emirates": "AE"
}

SCRIPT_DIR = Path(__file__).resolve().parent
base = f"{SCRIPT_DIR}/input/dataset_3_anon"
scan_folders = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22"]
if len(scan_folders) < 2:
    print("Error: Provide at least 2 scan folders to calculate churn.")
    sys.exit(1)

# --- 2. Data Ingestion ---
country_data = {c: {} for c in TARGET_COUNTRIES}

for day in scan_folders:
    day_path = os.path.join(base, day)
    if not os.path.isdir(day_path): continue
    for country in TARGET_COUNTRIES:
        path = f"{day_path}/{country}/stun_a_green_ips.txt"
        if os.path.exists(path):
            with open(path) as f:
                ips = {line.strip() for line in f if line.strip() and not line.startswith("#")}
                country_data[country][day] = ips

# --- 3. Calculate Turnover Churn ---
# Formula: (New IPs + Lost IPs) / Total Yesterday * 100
days_axis = scan_folders[1:]
plot_data = {}

for country in TARGET_COUNTRIES:
    # Use a list of tuples (date, value) to ensure data stays pinned to the right day
    country_plot_points = []
    
    # We loop through your input 'scan_folders' EXACTLY as provided
    for i in range(len(scan_folders) - 1):
        d1 = scan_folders[i]
        d2 = scan_folders[i+1]
        
        # Only calculate if BOTH days exist for this country
        if d1 in country_data[country] and d2 in country_data[country]:
            s1 = country_data[country][d1]
            s2 = country_data[country][d2]
            
            # Prevent division by zero if the first day had no IPs
            if len(s1) == 0:
                continue
                
            new_ips = len(s2 - s1)
            lost_ips = len(s1 - s2)
            churn_pc = ((new_ips + lost_ips) / len(s1)) * 100
            
            # Pin the churn value to the second day (d2)
            country_plot_points.append((d2, churn_pc))
    
    plot_data[country] = country_plot_points

# --- 4. Plotting (Single Combined Graph) ---
plt.figure(figsize=(14, 8))
ax = plt.gca() # Get current axes to modify the border

# Increase the border width (spines)
border_width = 2.5 # Adjust this value as needed
for spine in ax.spines.values():
    spine.set_linewidth(border_width)

colors = plt.cm.nipy_spectral(np.linspace(-0.025, 0.5, 11))

# markers = ['o', 's', '^', 'D']  # Circle, Square, Triangle, Diamond
markers = ['o', 'D', 's', '^',]
lines = ['dotted']
for i, country in enumerate(TARGET_COUNTRIES):
    points = plot_data[country]
    if points:
        x_vals = [str(idx + 1) for idx, _ in enumerate(points)]
        y_vals = [float(p[1]) for p in points]
        
        plt.plot(x_vals, y_vals, label=f"{COUNTRY_CODES.get(country,country)}", 
                 color=colors[i % len(colors)], linewidth=3, linestyle=lines[i % len(lines)], 
                 marker=markers[i % len(markers)], markersize=15, alpha=0.8,
                 markeredgecolor='white', markeredgewidth=1)
                 
# plt.title("Daily Network Turnover Churn (%) - All Countries Combined", fontsize=16, pad=15)
plt.ylabel("Churn Rate (%)", fontsize=30, fontweight='bold')

start_date_raw = scan_folders[0].split('_')[0]
end_date_raw = scan_folders[-1].split('_')[0]

# Grid and Styling
plt.grid(True, linestyle='--', alpha=0.6, color='black')
plt.xticks(fontsize=22, fontweight='bold', ha='center', rotation=-45)
plt.yticks(fontsize=22, fontweight='bold')
plt.ylim(-1, None) # Start at 0, let max scale naturally

# Place legend outside to the right for clarity
plt.legend(bbox_to_anchor=(0.5, -0.1), loc='upper center', prop={'weight': 'bold', 'size': 20}, ncol=7, frameon=False, columnspacing=1.0)

plt.tight_layout()
out_dir = f"{SCRIPT_DIR}/output"
os.makedirs(out_dir, exist_ok=True)
plt.savefig(f"{out_dir}/figure_4_combined_churn_percentage.png", dpi=300, bbox_inches='tight')
