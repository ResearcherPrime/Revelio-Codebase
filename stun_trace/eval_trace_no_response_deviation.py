import os
import re
import csv
import sys
import bisect
import ipaddress
from pathlib import Path

if len(sys.argv) != 3:
   print(f"Usage: python3 {sys.argv[0]} <traceroute_output_dir> <asn_prefix_csv>")
   sys.exit(1)

TRACE_DIR = sys.argv[1] # trace_output/United_Arab_Emirates
PREFIXES_CSV = sys.argv[2] # prefixes/United_Arab_Emirates.csv

SCRIPT_DIR = Path(__file__).resolve().parent

TRACE_PATH = Path(TRACE_DIR)

country = TRACE_PATH.parts[-2]

deviation_type = TRACE_PATH.parts[-1]

MIDDLEBOX_ROOT = os.path.join(
    SCRIPT_DIR,
    "middleboxes"
)

# ---------- ASN Mapping ----------

def load_asn_table(csv_path):

    intervals = []

    with open(csv_path, newline="") as f:

        reader = csv.DictReader(f)

        for row in reader:

            asn = row["ASN"].strip()
            prefix = row["Prefix"].strip()

            if not asn or not prefix:
                continue

            try:
                net = ipaddress.ip_network(prefix, strict=False)
            except ValueError:
                continue

            if net.version != 4:
                continue

            intervals.append((
                int(net.network_address),
                int(net.broadcast_address),
                net.prefixlen,
                asn
            ))

    intervals.sort(key=lambda e: e[0])

    return intervals


def build_lpm_index(intervals):

    return [iv[0] for iv in intervals], intervals


def lookup_asn(ip_str, starts, intervals):

    try:
        ip_int = int(ipaddress.IPv4Address(ip_str))
    except ValueError:
        return None

    hi = bisect.bisect_right(starts, ip_int)

    best_plen = -1
    best_asn = None

    for i in range(hi - 1, -1, -1):

        start, end, plen, asn = intervals[i]

        if end < ip_int:
            continue

        if plen > best_plen:
            best_plen = plen
            best_asn = asn

            if plen == 32:
                break

    return best_asn


# ---------- Traceroute Parsing ----------

def parse_traceroute(filename, dest_ip):

    hops = []
    reached_dest = False

    with open(filename) as f:

        for line in f:

            line = line.strip()

            m = re.search(r"outer=\s*([^\s]+)", line)

            if not m:
                continue

            hop = m.group(1)

            if hop == "NA":
                hop = "*"

            hops.append(hop)

            if hop == dest_ip:
                reached_dest = True

    return hops, reached_dest


def get_first_dest_index(hops, dest_ip):

    for i, hop in enumerate(hops):

        if hop == dest_ip:
            return i

    return None

# ---------- Check IP belong to country---
def check_country(ip, starts, intervals):
    asn = lookup_asn(
        ip,
        starts,
        intervals
    )
    return asn != None


# ---------- Load ASN DB ----------

intervals = load_asn_table(PREFIXES_CSV)
starts, intervals = build_lpm_index(intervals)

# ---------- Main Loop ----------

for app_dir in os.listdir(TRACE_DIR):

    app_trace_dir = os.path.join(
        TRACE_DIR,
        app_dir
    )

    if not os.path.isdir(app_trace_dir):
        continue

    app = os.path.basename(app_trace_dir)

    middleboxes = []

    guessed_ases = []

    likely_filtered = []

    for file in os.listdir(app_trace_dir):

        if not file.endswith("_p1.txt"):
            continue

        ip = file.replace("_p1.txt", "")

        p1_file = os.path.join(
            app_trace_dir,
            f"{ip}_p1.txt"
        )

        p2_file = os.path.join(
            app_trace_dir,
            f"{ip}_p2.txt"
        )
        if not os.path.exists(p2_file):
            continue

        likely_filtered.append(ip)

        hops_p1, p1_reached = parse_traceroute(p1_file, ip)
        hops_p2, p2_reached = parse_traceroute(p2_file, ip)

        # Keep only:
        # p1 -> does NOT reach destination
        # p2 -> DOES reach destination

        if (not p1_reached) and p2_reached:

            print("\n==========")
            print("IP:", ip)

            first_dest_index = get_first_dest_index(hops_p2, ip)

            print("First destination index in P2:",
                first_dest_index)

            if first_dest_index is None:
                continue

            if first_dest_index >= len(hops_p1):
                continue

            p1_same_index_hop = hops_p1[first_dest_index]

            # ---------- Case 1 ----------
            # P1 has visible IP at same index

            if p1_same_index_hop != "*":

                print("Possible middlebox:",
                    p1_same_index_hop)

                if check_country(ip, starts, intervals):
                    middleboxes.append(
                        (ip, p1_same_index_hop)
                    )
                else:
                    continue

            # ---------- Case 2 ----------
            # P1 has '*'
            # Walk backwards in P2

            prev_hop_p2 = None

            for i in range(first_dest_index - 1, -1, -1):

                if hops_p2[i] != "*":

                    prev_hop_p2 = hops_p2[i]
                    prev_index = i
                    break

            if prev_hop_p2 is None:
                continue

            print("Nearest previous visible P2 hop:",
                prev_hop_p2)

            # ---------- ASN comparison ----------

            prev_hop_asn = lookup_asn(
                prev_hop_p2,
                starts,
                intervals
            )

            dest_asn = lookup_asn(
                ip,
                starts,
                intervals
            )

            print("Previous hop ASN:",
                prev_hop_asn)

            print("Destination ASN:",
                dest_asn)

            # Keep only ASN-matching cases

            if (
                prev_hop_asn is not None
                and dest_asn is not None
                and prev_hop_asn == dest_asn
            ):

                guessed_ases.append(
                    (ip, dest_asn)
                )

                print("ASN MATCH")

            else:

                print("ASN MISMATCH -> rejected")

                continue

        else:
            print("Rejected:", ip)

    # Output to files

    output_dir = os.path.join(
        MIDDLEBOX_ROOT,
        country,
        deviation_type
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    # print("\n==========")
    # print("Middleboxes observed:")

    middlebox_file = os.path.join(
        output_dir,
        f"{app}_middleboxes.txt"
    )

    with open(middlebox_file, "w") as f:

        for entry in middleboxes:

            ip, mb = entry

            f.write(
                f"Dest_IP->{ip}, "
                f"Middlebox_IP->{mb}\n"
            )

    # print("\n==========")
    # print("Destination IPs with matching ASN:")
    
    guessed_file = os.path.join(
        output_dir,
        f"{app}_guessed_asn.txt"
    )

    with open(guessed_file, "w") as f:

        for ip, asn in guessed_ases:

            f.write(
                f"Dest_IP->{ip}, "
                f"Guessed_AS->{asn}\n"
            )

    # print("\n==========")
    # print("Likely filtered destination IPs:")

    likely_file = os.path.join(
        output_dir,
        f"{app}_likely_filtered_dest_IP.txt"
    )

    with open(likely_file, "w") as f:

        for ip in likely_filtered:

            f.write(
                f"Dest_IP->{ip}\n"
            )

