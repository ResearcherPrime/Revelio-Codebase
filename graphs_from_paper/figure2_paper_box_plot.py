import os
import matplotlib.pyplot as plt
import numpy as np

# --- 1. Settings & Data Ingestion ---
base = "input/dataset_3_anon"
scan_folders =  ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22"]

country_data = {}

for folder in scan_folders:
    day_path = os.path.join(base, folder)
    if not os.path.isdir(day_path):
        continue

    for country in os.listdir(day_path):
        path = f"{day_path}/{country}/stun_a_green_ips.txt"
        if not os.path.exists(path):
            continue

        with open(path) as f:
            # Count unique IPs, ignoring comments/empty lines
            ips = {line.strip() for line in f if line and not line.startswith("#")}
        
        country_data.setdefault(country, []).append(len(ips))

# --- 2. Filtering & Sorting ---
TARGET_COUNTRIES = [
    "Azerbaijan", "Estonia", "Iraq", "Kazakhstan", "Kyrgyzstan", 
    "Mexico", "Myanmar", "Qatar", "South_Africa", "Egypt", 
    "Indonesia", "Jordan", "Kuwait", "Malaysia", "Morocco", 
    "Pakistan", "Saudi_Arabia", "Turkey", "United_Arab_Emirates"
]

COUNTRY_CODES = {
    "Azerbaijan": "AZ", "Estonia": "EE", "Iraq": "IQ", "Kazakhstan": "KZ",
    "Kyrgyzstan": "KG", "Mexico": "MX", "Myanmar": "MM", "Qatar": "QA",
    "South_Africa": "ZA", "Egypt": "EG", "Indonesia": "ID", "Jordan": "JO",
    "Kuwait": "KW", "Malaysia": "MY", "Morocco": "MA", "Pakistan": "PK",
    "Saudi_Arabia": "SA", "Turkey": "TR", "United_Arab_Emirates": "AE"
}

# Keep countries with at least 2 data points
filtered_countries = [c for c in TARGET_COUNTRIES if c in country_data and len(country_data[c]) >= 2]

# Sort countries by their mean count (descending) for better visual flow
filtered_countries.sort(key=lambda c: np.mean(country_data[c]), reverse=True)

# --- 3. Visualization ---
plt.figure(figsize=(18, 8)) # Wider figure to accommodate spacing

ax = plt.gca()
border_width = 2.5
for spine in ax.spines.values():
    spine.set_linewidth(border_width)

# Calculate stats
means = [np.mean(country_data[c]) for c in filtered_countries]
stds = [np.std(country_data[c]) for c in filtered_countries]

# INCREASE SPACING: Multiplying index by 1.5 spreads the labels and bars apart
x_pos = np.arange(len(filtered_countries)) * 1.5 

# Create bars with reduced width for a cleaner look
bars = plt.bar(
    x_pos, 
    means, 
    yerr=stds, 
    width=0.8,    # Thinner bars
    capsize=5, 
    color='#a6a6a6', 
    edgecolor='black',
    linewidth=border_width,
    zorder=3,
    error_kw=dict(lw=border_width, capthick=border_width)
)

# Apply Country Codes to X-Ticks
xtick_labels = [COUNTRY_CODES.get(c, c) for c in filtered_countries]

plt.xticks(
    x_pos, 
    xtick_labels, 
    rotation=0,   # Horizontal labels for better readability
    fontsize=26, 
    fontweight="bold"
)

# Final Formatting
plt.ylabel("Unique STUN IPs", fontsize=30, fontweight="bold")
plt.yticks(fontsize=26, fontweight="bold")
ax.tick_params(width=border_width, length=6)

# Add margin to the left and right edges
plt.xlim(min(x_pos) - 1, max(x_pos) + 1)

plt.grid(True, axis="both", linestyle="-", linewidth=0.8, alpha=0.8, color='black', zorder=0)
plt.tight_layout()

# --- 4. Save Logic ---
out_dir = "output"
os.makedirs(out_dir, exist_ok=True)
save_path = f"{out_dir}/global_count_barchart.png"
plt.savefig(save_path, dpi=600, bbox_inches='tight')

print(f"Success! Plot saved to: {save_path}")
