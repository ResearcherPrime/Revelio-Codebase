import os
import csv
from collections import defaultdict
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PER_COUNTRY_DIR = f"{SCRIPT_DIR}/output/per_country_csv"
OUT_DIR = f"{SCRIPT_DIR}/output"
OUT_FILE = "domain_filtering_percentage.csv"

# ---------------- DOMAIN → APP ----------------
DOMAIN_TO_APP = {
    "whatsapp.com": "Whatsapp",
    "telegram.org": "Telegram",
    "viber.com": "Viber",
    "signal.org": "Signal",
    "messenger.com": "Messenger",
    "instagram.com": "Instagram",
    "slack.com": "Slack",
    "dialpad.com": "Dialpad",
    "webex.com": "Webex",
    "jitsi.org": "Jitsi",
    "wire.com": "Wire",
}

os.makedirs(OUT_DIR, exist_ok=True)

# (country, domain, source) → list of daily probe filtering percentages
probe_daily_percentages = defaultdict(list)

# (country, domain, source) → list of daily ASN filtering percentages
asn_daily_percentages = defaultdict(list)

for fname in os.listdir(PER_COUNTRY_DIR):
    if not fname.endswith(".csv"):
        continue

    country = fname.replace(".csv", "")
    path = os.path.join(PER_COUNTRY_DIR, fname)

    # (domain, day, source) → probe outcome counts
    probe_counts_per_day = defaultdict(lambda: {"uncensored": 0, "filtered": 0})

    # (domain, day, source, asn) → probe outcome counts
    asn_probe_counts_per_day = defaultdict(lambda: {"uncensored": 0, "filtered": 0})

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = row["domain"]
            day = row["day"]
            source = row["source"]
            asn = row["asn"]
            outcome = row["outcome"]

            if outcome == "Uncensored":
                probe_counts_per_day[(domain, day, source)]["uncensored"] += 1
                asn_probe_counts_per_day[(domain, day, source, asn)]["uncensored"] += 1
            elif outcome == "Filtered":
                probe_counts_per_day[(domain, day, source)]["filtered"] += 1
                asn_probe_counts_per_day[(domain, day, source, asn)]["filtered"] += 1

    # -------- probe filtering % per day --------
    per_day_probe_percentage = defaultdict(list)

    for (domain, day, source), counts in probe_counts_per_day.items():
        total = counts["uncensored"] + counts["filtered"]
        if total == 0:
            continue

        pct = (counts["filtered"] / total) * 100
        per_day_probe_percentage[(domain, source)].append(pct)

    for (domain, source), day_values in per_day_probe_percentage.items():
        probe_daily_percentages[(country, domain, source)].append(
            sum(day_values) / len(day_values)
        )

    # -------- ASN filtering % per day --------
    asn_filtering_flags_per_day = defaultdict(dict)
    # key: (domain, day, source) → {asn → 0/1}

    for (domain, day, source, asn), counts in asn_probe_counts_per_day.items():
        total = counts["uncensored"] + counts["filtered"]
        if total == 0:
            continue

        filtered_fraction = counts["filtered"] / total
        asn_filtering_flags_per_day[(domain, day, source)][asn] = (
            1 if filtered_fraction > 0.10 else 0     # If filtered IP count in an AS is more than 10 % then mark AS as filtered
        )

    for (domain, day, source), asn_flags in asn_filtering_flags_per_day.items():
        total_asns = len(asn_flags)
        if total_asns == 0:
            continue

        daily_asn_pct = (sum(asn_flags.values()) / total_asns) * 100
        asn_daily_percentages[(country, domain, source)].append(daily_asn_pct)

# -------- WRITE FINAL TABLE --------
out_path = os.path.join(OUT_DIR, OUT_FILE)

with open(out_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "country",
        "app",
        "domain",
        "source",
        "avg_filtering_percentage",
        "avg_as_filtering_percentage",
    ])

    for (country, domain, source), probe_vals in sorted(probe_daily_percentages.items()):
        app = DOMAIN_TO_APP.get(domain, "Other")

        as_vals = asn_daily_percentages.get((country, domain, source), [])
        avg_as_pct = sum(as_vals) / len(as_vals) if as_vals else ""

        writer.writerow([
            country,
            app,
            domain,
            source,
            sum(probe_vals) / len(probe_vals),
            avg_as_pct,
        ])

print(f"[DONE] Wrote table to {out_path}")

# Cleaning up temporary files
shutil.rmtree(PER_COUNTRY_DIR)
