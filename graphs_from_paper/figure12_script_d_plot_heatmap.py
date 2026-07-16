import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.colors import ListedColormap
from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
CSV_PATH = f"{SCRIPT_DIR}/output/domain_filtering_percentage.csv"
OUT_DIR = f"{SCRIPT_DIR}/output"
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(CSV_PATH)

def plot_heatmap(source, prefix):
    sub = df[df["source"] == source].copy()
    if sub.empty:
        return

    # ---------- DATA ----------
    pivot_probe = pd.pivot_table(
        sub,
        index="domain",
        columns="country",
        values="avg_filtering_percentage",
        aggfunc="mean"
    )
    pivot_probe = pivot_probe.replace(0, np.nan)

    pivot_as = pd.pivot_table(
        sub,
        index="domain",
        columns="country",
        values="avg_as_filtering_percentage",
        aggfunc="mean"
    )

    domain_to_app = sub.drop_duplicates("domain").set_index("domain")["app"]

    domain_mean = pivot_probe.mean(axis=1, skipna=True)
    app_mean = domain_mean.groupby(domain_to_app).mean().sort_values(ascending=False)

    domain_order = []
    app_boundaries = []
    cursor = 0

    for app in app_mean.index:
        domains = domain_mean[domain_to_app == app] \
            .sort_values(ascending=False).index.tolist()
        if not domains:
            continue
        start = cursor
        domain_order.extend(domains)
        cursor += len(domains)
        app_boundaries.append((app, start, cursor))

    country_order = pivot_probe.mean(axis=0, skipna=True).sort_values(ascending=False).index

    pivot_probe = pivot_probe.loc[domain_order, country_order]
    pivot_as = pivot_as.loc[domain_order, country_order]

    probe_data = pivot_probe.values.astype(float)
    as_data = pivot_as.values.astype(float)

    # ---------- FIGURE ----------
    fig_width = max(30, len(country_order))
    fig_height = max(10, len(domain_order))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    cmap = plt.get_cmap("YlOrRd").copy()
    cmap.set_under("#e6e6e6")
    cmap.set_bad("white")

    im = ax.imshow(
        probe_data,
        cmap=cmap,
        aspect="auto",
        vmin=2,
        vmax=100
    )

    ax.set_xticks(np.arange(-0.5, probe_data.shape[1], 1), minor=True)
    ax.set_yticks(np.arange(-0.5, probe_data.shape[0], 1), minor=True)

    ax.grid(which="minor", color="black", linestyle="-", linewidth=1)
    ax.tick_params(which="minor", bottom=False, left=False)

    # ---------- AXES ----------
    ax.set_xticks(np.arange(len(country_order)))
    ax.set_xticklabels(
        country_order,
        rotation=45,
        ha="right",
        fontsize=26,
        fontweight="bold"
    )
    ax.tick_params(axis='y', which='both', left=False, labelleft=False)

    # ---------- COLORBAR ----------
    cax = fig.add_axes([0.25, 0, 0.5, 0.025])  # left, bottom, width, height
    cbar = fig.colorbar(im, cax=cax, orientation="horizontal", extend="min")
    cbar.set_label("Probe Filtering Percentage (%)",fontsize=26, fontweight="bold")
    cbar.ax.tick_params(labelsize=22, width=2, length=8)

    # ---------- CELL ANNOTATIONS (AS %) ----------
    for i in range(probe_data.shape[0]):
        for j in range(probe_data.shape[1]):
            if np.isnan(as_data[i, j]):
                continue

            # val = int(round(as_data[i, j]))
            val = f"{float(as_data[i, j]):.1f}"
            if int(as_data[i, j]) == 100:
                val = 100 #int(val)
            if float(as_data[i, j]) == 0:
                continue
            ax.text(
                j, i, f"{val}",
                ha="center", va="center",
                fontsize=18, fontweight='bold',
                color="white" if probe_data[i, j] >= 30 else "black"
            )

    # ---------- APP LABELS & SEPARATORS ----------
    for app, start, end in app_boundaries:
        ax.axhline(start - 0.5, color="black", linewidth=2)
        ax.text(
            -0.02, (start + end - 1) / 2,
            app,
            transform=ax.get_yaxis_transform(),
            va="center", ha="right",
            fontsize=26, fontweight="bold"
        )

    plt.subplots_adjust(left=0.25, right=0.75, top=0.85, bottom=0.15)

    out = os.path.join(OUT_DIR, f"{prefix}_{source}_filtering_heatmap.png")
    plt.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"[OK] Wrote {out}")

# Run
plot_heatmap("http", "figure12_a")
plot_heatmap("https", "figure12_b")

os.remove(CSV_PATH)
