import sys
from collections import Counter

input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file) as f:
    lines = [line.strip() for line in f if line.strip()]

counts = Counter(lines)

with open(output_file, "w") as f:
    for line, count in counts.items():
        f.write(f"{line},{count}\n")

