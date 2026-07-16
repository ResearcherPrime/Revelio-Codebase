import pandas as pd
import os
from pathlib import Path

# --- Paths ---
SCRIPT_DIR = Path(__file__).resolve().parent

input_file = f"{SCRIPT_DIR}/input/table_3_input.csv"
output_dir = f"{SCRIPT_DIR}/output"
output_file = f"{output_dir}/table_3_output.csv"

# --- Validate input ---
if not os.path.exists(input_file):
    raise FileNotFoundError(
        f"Input CSV not found: {input_file}"
    )

# --- Load input ---
df = pd.read_csv(input_file)

# Remove accidental spaces from column names
df.columns = df.columns.str.strip().str.replace(" ", "")

# --- Calculate percentages ---
output_df = pd.DataFrame({
    "Country": df["COUNTRY"].str.replace("_", " "),
    "Filtered AS (%)": (
        df["FILTERED_ASes"] / df["TOTAL_ASes"] * 100
    ).round(2),
    "AS with Middlebox (%)": (
        df["MIDDLEBOX_ASes"] / df["TOTAL_ASes"] * 100
    ).round(2),
    "Filtered STUN (%)": (
        df["FILTERED_STUN_SERVERS"]
        / df["TOTAL_STUN_SERVERS"]
        * 100
    ).round(2),
})

# --- Export ---
os.makedirs(output_dir, exist_ok=True)

output_df.to_csv(
    output_file,
    index=False
)

print(f"[✓] Table 3 CSV created successfully: {output_file}")
