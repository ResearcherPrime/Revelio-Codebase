import json
import sys
import os
import csv
from collections import defaultdict

# ---------- Outcome → Category mapping (dashboard-faithful) ----------
UNCENSORED_PREFIXES = {
    "expected/match",
    "expected/trusted_host",
}

DOUBT_PREFIXES = {
    "content/body_mismatch",
    "content/header_mismatch",
    "content/status_mismatch",
    "content/tls_mismatch",
    "dns.error",
    "dns.timedout",
    "tls.connerror",
    "tls/timeout",
    "tls/tls.failed",
    "dial/ip.host_no_route",
    "dial/ip.network_unreachable",
    "dial/tcp.refused",
    "dial/tcp.reset",
    "dns.hostunreach",
}

FILTERED_PREFIXES = {
    "content/blockpage",
    "dns.connrefused",
    "dns.error:",        # filtered DNS errors are parameterized
    "http.blockpage",
    "ip.empty",
    "ip.invalid",
    "read/http.empty",
    "read/tcp.reset",
    "read/timeout",
    "tls.badca",
    "tls.baddomain",
    "write/tcp.reset",
}

def categorize(outcome):
    for p in UNCENSORED_PREFIXES:
        if outcome.startswith(p):
            return "Uncensored"
    for p in FILTERED_PREFIXES:
        if outcome.startswith(p):
            return "Filtered"
    for p in DOUBT_PREFIXES:
        if outcome.startswith(p):
            return "Doubt"
    return "Doubt"   # conservative default

def conclude_category(categories):
    if "Uncensored" in categories:
        return "Uncensored"
    elif "Filtered" in categories:
        return "Filtered"
    else:
        return "Doubt"

json_path = sys.argv[1]

# Infer domain + source from filename
base = os.path.basename(json_path)
domain = base.replace("_http.json", "").replace("_https.json", "")
source = "https" if "_https.json" in base else "http"

# date -> (ip,asn) -> set(categories)
daily_ip_asn_categories = defaultdict(lambda: defaultdict(set))

with open(json_path) as f:
    j = json.load(f)

for row in j.get("data", {}).get("hyperquack", []):
    date = row.get("date")
    ip = row.get("serverIp")
    asn = row.get("serverAsn")
    outcome = row.get("outcome")

    if not date or not ip or not asn or not outcome:
        continue

    category = categorize(outcome)
    daily_ip_asn_categories[date][(ip, asn)].add(category)

# -------- PRINT FINAL CATEGORY PER IP,ASN PER DAY --------
OUT_DIR = "plotting/output/per_json_csv"
os.makedirs(OUT_DIR, exist_ok=True)

country = os.path.basename(os.path.dirname(json_path))
csv_name = f"{country}_{os.path.basename(json_path).replace('.json', '.csv')}"
csv_path = os.path.join(OUT_DIR, csv_name)

with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["day", "ip", "asn", "outcome", "domain", "source"])

    for date in sorted(daily_ip_asn_categories):
        for (ip, asn), cats in daily_ip_asn_categories[date].items():
            final_cat = conclude_category(cats)
            writer.writerow([date, ip, asn, final_cat, domain, source])
