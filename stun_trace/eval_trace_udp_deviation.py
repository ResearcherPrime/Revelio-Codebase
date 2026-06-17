import os
import re
import csv
import sys
import bisect
import ipaddress
import json
import requests
from pathlib import Path

if len(sys.argv) != 3:
   print(f"Usage: python3 {sys.argv[0]} <traceroute_output_dir> <asn_prefix_csv>")
   sys.exit(1)

TRACE_DIR = sys.argv[1] # trace_output/United_Arab_Emirates
PREFIXES_CSV = sys.argv[2] # prefixes/United_Arab_Emirates.csv

country = Path(TRACE_DIR).parts[-2]
print(country)

deviation_type = Path(TRACE_DIR).parts[-1]

SCRIPT_DIR = Path(__file__).resolve().parent

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
                net = ipaddress.ip_network(
                    prefix,
                    strict=False
                )

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
        ip_int = int(
            ipaddress.IPv4Address(ip_str)
        )

    except ValueError:
        return None

    hi = bisect.bisect_right(
        starts,
        ip_int
    )

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

# ---------- Check IP belong to country---
def check_country(ip, starts, intervals):
    asn = lookup_asn(
        ip,
        starts,
        intervals
    )
    return asn != None

# ---------- Traceroute Parsing ----------

def parse_traceroute(filename, dest_ip):

    hops = []

    hop_is_udp = []

    reached_dest = False

    reached_with_udp = False

    with open(filename) as f:

        for line in f:

            line = line.strip()

            m = re.search(
                r"outer=\s*([^\s]+)",
                line
            )

            if not m:
                continue

            hop = m.group(1)

            if hop == "NA":
                hop = "*"

            hops.append(hop)

            is_udp = ("NON-ICMP UDP" in line)

            hop_is_udp.append(is_udp)

            if hop == dest_ip:

                reached_dest = True

                if is_udp:
                    reached_with_udp = True

    return (
        hops,
        reached_dest,
        reached_with_udp,
        hop_is_udp
    )

def count_udp_hops(dest, hops, is_udp):
    count = 0
    for i, hop in enumerate(hops):
        if (hop == "*"):
            continue
        if(is_udp[i] and hop == dest):
            count += 1
    return count

def get_first_dest_index(hops, dest_ip):

    for i, hop in enumerate(hops):

        if hop == dest_ip:
            return i

    return None


# ---------- Load ASN DB ----------

intervals = load_asn_table(PREFIXES_CSV)

starts, intervals = build_lpm_index(
    intervals
)

# ---------- Main Loop ----------

for app_dir in os.listdir(TRACE_DIR):

    app_trace_dir = os.path.join(
        TRACE_DIR,
        app_dir
    )

    if not os.path.isdir(app_trace_dir):
        continue

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

        app = os.path.basename(
            app_trace_dir
        )
        hops_p1, p1_reached, p1_udp, hop_p1_is_udp = (
            parse_traceroute(
                p1_file,
                ip
            )
        )

        hops_p2, p2_reached, p2_udp, hop_p2_is_udp = (
            parse_traceroute(
                p2_file,
                ip
            )
        )

        # -----------------------------------------
        # Step-1
        # P1 must reach via UDP
        # -----------------------------------------

        if not (p1_reached and p1_udp):
            print(
                "Rejected (P1 no UDP destination response):",
                ip
            )

            continue

        print("\n==========")
        print("P1 reached destination via UDP:", ip)

        # -----------------------------------------
        # CASE-1
        # P2 did NOT reach destination
        # -----------------------------------------

        if not p2_reached:
            likely_filtered.append(ip)

            print("CASE-1: P2 did NOT reach destination")

            last_visible_idx = None

            last_visible_ip = None

            for i in range(len(hops_p2) - 1, -1, -1):
                if hops_p2[i] != "*":

                    last_visible_idx = i

                    last_visible_ip = hops_p2[i]

                    break

            if last_visible_idx is None:

                print(
                    "Rejected: No visible hop in P2"
                )

                continue

            print(
                "Last visible P2 hop:",
                last_visible_ip
            )

            print(
                "Last visible P2 index:",
                last_visible_idx
            )

            next_idx = last_visible_idx + 1

            if next_idx >= len(hops_p1):

                print(
                    "Rejected: No next index in P1"
                )

                continue

            candidate_ip = hops_p1[next_idx]

            print(
                "P1 next-index hop:",
                candidate_ip
            )

            if (candidate_ip == "*" or candidate_ip == ip):

                candidate_asn = lookup_asn(candidate_ip, starts, intervals)
                dest_asn = lookup_asn(ip, starts, intervals)

                if(candidate_asn and dest_asn and candidate_asn == dest_asn):
                    print(
                        "Guessed ASN:",
                        candidate_asn
                    )

                    guessed_ases.append(
                        (
                            ip,
                            candidate_asn
                        )
                    )

            else:
                if check_country(candidate_ip, starts, intervals):
                    print(
                        "Middlebox detected:",
                        candidate_ip
                    )

                    middleboxes.append(
                        (
                            ip,
                            candidate_ip
                        )
                    )

        # -----------------------------------------
        # CASE-2
        # P2 reached via UDP
        # -----------------------------------------

        elif p2_udp:

            print(
                "CASE-2: P2 reached destination via UDP"
            )

            p1_udp_count = count_udp_hops(ip, hops_p1, hop_p1_is_udp)

            p2_udp_count = count_udp_hops(ip, hops_p2, hop_p2_is_udp)

            ratio = 0

            if p1_udp_count > 0:

                ratio = (
                    p2_udp_count
                    / p1_udp_count
                )

            print(
                "P1 UDP count:",
                p1_udp_count
            )

            print(
                "P2 UDP count:",
                p2_udp_count
            )

            print(
                "UDP ratio:",
                ratio
            )

            if ratio >= 0.6: ## Add in other code for eval.py

                print(
                    "Rejected: P2 UDP still >=90% of P1"
                )

                continue

            likely_filtered.append(ip)

            print(
                "Accepted: Possible UDP throttling"
            )

            candidate_ip = None

            candidate_idx = None

            for i in range(
                len(hops_p2) - 1,
                -1,
                -1
            ):
                if hops_p2[i] != ip and hops_p2[i]!="*":

                    candidate_ip = hops_p2[i]

                    candidate_idx = i

                    break
                # print(hops_p2[i])
            if (
                candidate_ip is None
                or candidate_ip == "*"
            ):

                print(
                    "Rejected: No candidate hop found"
                )

                continue

            print(
                "Candidate hop:",
                candidate_ip
            )

            print(
                "Candidate index:",
                candidate_idx
            )

            if candidate_idx >= len(hops_p1):

                print(
                    "Rejected: Candidate index exceeds P1"
                )

                continue

            p1_same_ip = hops_p1[
                candidate_idx
            ]

            print(
                "P1 same-index hop:",
                p1_same_ip
            )

            # Exact Match

            if p1_same_ip == candidate_ip:

                candidate_asn = lookup_asn(
                    candidate_ip,
                    starts,
                    intervals
                )

                if candidate_asn:

                    print(
                        "Middlebox detected:",
                        candidate_ip,
                        "ASN:",
                        candidate_asn
                    )

                    middleboxes.append(
                        (
                            ip,
                            candidate_ip,
                            # candidate_asn
                        )
                    )

                else:

                    print(
                        "Rejected: ASN unknown for candidate"
                    )

            # ASN Guess

            else:

                candidate_asn = lookup_asn(
                    candidate_ip,
                    starts,
                    intervals
                )

                dest_asn = lookup_asn(
                    ip,
                    starts,
                    intervals
                )

                print(
                    "Candidate ASN:",
                    candidate_asn
                )

                print(
                    "Destination ASN:",
                    dest_asn
                )

                if (
                    candidate_asn
                    and dest_asn
                    and candidate_asn == dest_asn
                ):

                    print(
                        "Guessed ASN:",
                        candidate_asn
                    )

                    guessed_ases.append(
                        (
                            ip,
                            candidate_asn
                        )
                    )

                else:

                    print(
                        "Rejected: ASN mismatch"
                    )

                    continue

        # -----------------------------------------
        # CASE-3
        # P2 reached but NOT via UDP
        # -----------------------------------------

        else:

            print(
                "CASE-3: P2 reached destination but NOT via UDP"
            )

            first_dest_index = (
                get_first_dest_index(
                    hops_p2,
                    ip
                )
            )

            print(
                "First destination index in P2:",
                first_dest_index
            )

            if first_dest_index is None:
                continue

            likely_filtered.append(ip)

            if first_dest_index >= len(hops_p1):
                continue

            p1_same_index_hop = hops_p1[
                first_dest_index
            ]

            # Visible IP in P1

            if p1_same_index_hop != "*" and p1_same_index_hop != ip and check_country(p1_same_index_hop, starts, intervals):

                print(
                    "Possible middlebox:",
                    p1_same_index_hop
                )

                middleboxes.append(
                    (
                        ip,
                        p1_same_index_hop
                    )
                )

                continue

            # Walk backwards in P2

            prev_hop_p2 = None

            for i in range(
                first_dest_index - 1,
                -1,
                -1
            ):

                if hops_p2[i] != "*":

                    prev_hop_p2 = hops_p2[i]

                    prev_index = i

                    break

            if prev_hop_p2 is None:
                continue

            print(
                "Nearest previous visible P2 hop:",
                prev_hop_p2
            )

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

            print(
                "Previous hop ASN:",
                prev_hop_asn
            )

            print(
                "Destination ASN:",
                dest_asn
            )

            if (
                prev_hop_asn is not None
                and dest_asn is not None
                and prev_hop_asn == dest_asn
            ):

                guessed_ases.append(
                    (
                        ip,
                        dest_asn
                    )
                )

                print("ASN MATCH")

            else:

                print(
                    "ASN MISMATCH -> rejected"
                )

                continue
    
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

