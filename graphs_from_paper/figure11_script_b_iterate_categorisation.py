import os
import subprocess
import csv
import glob

TRUSTED_PARSER = "plotting/figure11_script_a_categorise_outcomes.py"
PER_JSON_DIR = "plotting/output/per_json_csv"
FINAL_OUT_DIR = "plotting/output/per_country_csv"
RAW_DIR = "plotting/input/dataset_4"

os.makedirs(FINAL_OUT_DIR, exist_ok=True)
os.makedirs(PER_JSON_DIR, exist_ok=True)

COUNTRIES=[
    "AZ",  # Azerbaijan
    "EG",  # Egypt
    "EE",  # Estonia
    "ID",  # Indonesia
    "IQ",  # Iraq
    "JO",  # Jordan
    "KZ",  # Kazakhstan
    "KW",  # Kuwait
    "KG",  # Kyrgyzstan
    "MY",  # Malaysia
    "MX",  # Mexico
    "MA",  # Morocco
    "MM",  # Myanmar
    "PK",  # Pakistan
    "QA",  # Qatar
    "SA",  # Saudi Arabia
    "ZA",  # South Africa
    "TR",  # Turkey
    "AE",  # United Arab Emirates
    "CN",  # China
    "RU",  # Russia
    "OM",  # Oman
    "TM",  # Turkmenistan
]
APP_ANCHORS = [
    "whatsapp.com",
    "telegram.org",
    "viber.com",
    "signal.org",
    "messenger.com",
    "instagram.com",
    "slack.com",
    "dialpad.com",
    "webex.com",
    "jitsi.org",
    "wire.com",
]

for country in sorted(COUNTRIES):
    country_dir = os.path.join(RAW_DIR, country)

    # 1. Run trusted parser on all JSONs in the country folder
    json_files = (
        glob.glob(os.path.join(country_dir, "*_http.json")) +
        glob.glob(os.path.join(country_dir, "*_https.json"))
    )

    for jf in json_files:
        base = os.path.basename(jf)
        domain = base.replace("_http.json", "").replace("_https.json", "")
        if domain in APP_ANCHORS:
            subprocess.run(["python3", TRUSTED_PARSER, jf], check=True)

    # 2. Merge ONLY this country's CSVs
    final_csv = os.path.join(FINAL_OUT_DIR, f"{country}.csv")

    csv_files = glob.glob(os.path.join(PER_JSON_DIR, f"{country}_*.csv"))

    with open(final_csv, "w", newline="") as fout:
        writer = None

        for cf in sorted(csv_files):
            with open(cf) as fin:
                reader = csv.reader(fin)
                header = next(reader)

                if writer is None:
                    writer = csv.writer(fout)
                    writer.writerow(header)

                for row in reader:
                    writer.writerow(row)

    print(f"[DONE] Country CSV written: {final_csv}")

