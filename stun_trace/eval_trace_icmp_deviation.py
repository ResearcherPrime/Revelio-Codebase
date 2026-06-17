import os
import re
import csv
import bisect
import ipaddress
import sys
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

# --------------------------------------------------
# ASN Mapping
# --------------------------------------------------

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

            intervals.append(
                (
                    int(net.network_address),
                    int(net.broadcast_address),
                    net.prefixlen,
                    asn
                )
            )

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


# --------------------------------------------------
# Traceroute Parsing
# --------------------------------------------------

def parse_traceroute(filename, dest_ip):

    hops = []

    ttl_expire = []

    dest_unreach = []

    reached_dest = False

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

            is_ttl_expire = "t=11" in line

            is_dest_unreach = "t=3" in line

            ttl_expire.append(is_ttl_expire)

            dest_unreach.append(is_dest_unreach)

            if hop == dest_ip:
                reached_dest = True

    return (
        hops,
        ttl_expire,
        dest_unreach,
        reached_dest
    )


# --------------------------------------------------
# Routing Loop Detection
# --------------------------------------------------

def detect_routing_loop(hops, hop_types, ip):

    # if len(hop_types) > 0 and hop_types[-1]:

    #     return True, "Last hop ICMP t=11"

    # tail = hops[-7:]

    counts = {}

    for i, hop in enumerate(hops):

        if hop == "*" or hop == ip or (hop_types[i] == False):
            continue

        counts[hop] = counts.get(hop, 0) + 1

        if counts[hop] >= 3:
            
            return True, f"Repeated hop: {hop}"

    return False, None

def count_icmp11(path, hop_types):
    counts = {}
    routing_loop_ttls = 0

    for hop in path:
        if hop == "*" or hop == ip:
            continue

        counts[hop] = counts.get(hop, 0) + 1
    
    for i,hop in enumerate(path):
        if hop == "*" or hop == ip:
            continue

        if(counts.get(hop, 0) > 1 and hop_types[i]):
            routing_loop_ttls+=1
    
    return routing_loop_ttls

# --------------------------------------------------
# Find Middlebox Candidate
# --------------------------------------------------

def find_middlebox_candidate(hops):

    counts = {}

    for hop in hops:

        if hop == "*":
            continue

        counts[hop] = counts.get(hop, 0) + 1

    for i,hop in enumerate(hops):

        if hop == "*":
            continue

        if counts[hop] >= 3:
            return i-1

    return None

def check_country(ip, starts, intervals):
    asn = lookup_asn(
        ip,
        starts,
        intervals
    )
    return asn != None

# --------------------------------------------------
# Load ASN DB
# --------------------------------------------------

intervals = load_asn_table(PREFIXES_CSV)

starts, intervals = build_lpm_index(intervals)

# --------------------------------------------------
# Main Loop
# --------------------------------------------------

for app_dir in os.listdir(TRACE_DIR):

    app_trace_dir = os.path.join(
        TRACE_DIR,
        app_dir
    )

    if not os.path.isdir(app_trace_dir):
        continue

    app = os.path.basename(app_trace_dir)

    detected_middleboxes = []

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

        (
            hops_p1, # Path of 30 hops
            ttl_expire_p1,
            dest_unreach_p1,
            p1_reached
        ) = parse_traceroute(
            p1_file,
            ip
        )

        (
            hops_p2,
            ttl_expire_p2,
            dest_unreach_p2,
            p2_reached
        ) = parse_traceroute(
            p2_file,
            ip
        )

        # We only study the cases for which the traceroute reaches any destination
        # if not p1_reached:
        #     continue

        p1_loop, p1_reason = detect_routing_loop(
            hops_p1,
            ttl_expire_p1,
            ip
        )

        p2_loop, p2_reason = detect_routing_loop(
            hops_p2,
            ttl_expire_p2,
            ip
        )

        p1_icmp11 = count_icmp11(hops_p1, ttl_expire_p1)

        p2_icmp11 = count_icmp11(hops_p2, ttl_expire_p2)

        # --------------------------------------------------
        # Case 1
        # --------------------------------------------------

        # We assume that destination is reachable in 40 hops
        # If ttl expired recieved at 40th hop, it implies routing loop
        # I

        if p1_loop and p2_loop:
            ratio = 0

            if p1_icmp11 > 0:

                ratio = p2_icmp11 / p1_icmp11

            if ratio < 0.6:
                likely_filtered.append(ip)

                print("\nAccepted:", ip)

                print(
                    "Reason: P2 has reduced ICMP11 count"
                )

                candidate_idx = find_middlebox_candidate(
                    hops_p2
                )

                # if candidate_ip:

                    # candidate_idx = None

                    # for i, hop in enumerate(hops_p2):

                    #     if hop == candidate_ip:

                    #         candidate_idx = i
                    #         break

                if candidate_idx is not None:
                    candidate_ip = hops_p2[candidate_idx]

                    if candidate_idx < len(hops_p1):

                        p1_same_ip = hops_p1[
                            candidate_idx
                        ]

                        if candidate_ip == "*":
                            if p1_same_ip == ip:
                                continue
                            elif p1_same_ip == "*":
                                for i in range(candidate_idx-1, -1, -1):
                                    if hops_p2[i] != "*":
                                        candidate_ip = hops_p2[i]
                                        break
                                if candidate_ip is not None:
                                    if check_country(candidate_ip, starts, intervals):
                                        print(
                                        "Middlebox detected:",
                                        candidate_ip
                                    )

                                    detected_middleboxes.append(
                                        (
                                            ip,
                                            candidate_ip,
                                            ""
                                        )
                                    )
                            elif check_country(p1_same_ip, starts, intervals):
                                print(
                                    "Middlebox detected:",
                                    p1_same_ip
                                )

                                detected_middleboxes.append(
                                    (
                                        ip,
                                        p1_same_ip,
                                        ""
                                    )
                                )
                            continue

                        # Exact Match

                        if p1_same_ip == candidate_ip:

                            asn = lookup_asn(
                                candidate_ip,
                                starts,
                                intervals
                            )

                            if asn:

                                print(
                                    "Middlebox detected:",
                                    candidate_ip,
                                    "ASN:",
                                    asn
                                )

                                detected_middleboxes.append(
                                    (
                                        ip,
                                        candidate_ip,
                                        asn
                                    )
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

                print("\nRejected:", ip)

                print(
                    "Reason: P2 ICMP11 still >=90% of P1"
                )

        # --------------------------------------------------
        # Case 2
        # --------------------------------------------------

        elif p1_loop and not p2_loop:

            print("\nAccepted:", ip)

            print(
                "Reason: P2 escaped routing loop"
            )

            unreach_idx = None

            for i in range(len(hops_p2)):

                if (
                    dest_unreach_p2[i]
                    and hops_p2[i] == ip
                ):

                    unreach_idx = i
                    break

            if unreach_idx is not None:
                likely_filtered.append(ip)

                if unreach_idx < len(hops_p1):

                    p1_candidate = hops_p1[
                        unreach_idx
                    ]

                    # Exact Match

                    if p1_candidate != "*":

                        candidate_asn = lookup_asn(
                            p1_candidate,
                            starts,
                            intervals
                        )

                        if candidate_asn:

                            print(
                                "Middlebox detected:",
                                p1_candidate,
                                "ASN:",
                                candidate_asn
                            )

                            detected_middleboxes.append(
                                (
                                    ip,
                                    p1_candidate,
                                    candidate_asn
                                )
                            )

                    # ASN Guess

                    else:

                        last_visible = None

                        for j in range(
                            unreach_idx - 1,
                            -1,
                            -1
                        ):

                            if hops_p2[j] != "*":

                                last_visible = hops_p2[j]

                                break

                        if last_visible:

                            candidate_asn = lookup_asn(
                                last_visible,
                                starts,
                                intervals
                            )

                            dest_asn = lookup_asn(
                                ip,
                                starts,
                                intervals
                            )

                            if (
                                candidate_asn
                                and dest_asn
                                and candidate_asn == dest_asn
                            ):

                                print(
                                    "Guessed Middlebox:",
                                    last_visible,
                                    "ASN:",
                                    candidate_asn
                                )

                                guessed_ases.append(
                                    (
                                        ip,
                                        candidate_asn
                                    )
                                )
            elif (not p2_reached):
                likely_filtered.append(ip)
                last_visible_idx = None

                last_visible_ip = None

                for i in range(len(hops_p2) - 1, -1, -1):
                    if (hops_p2[i] != "*" and hops_p2[i] != ip):

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

                if (
                    candidate_ip == "*"
                    or candidate_ip == ip
                ):
                    print(
                        "Middlebox not detected"
                    )

                    continue

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

                    detected_middleboxes.append(
                        (
                            ip,
                            candidate_ip,
                            candidate_asn
                        )
                    )
                else:
                    continue
        
        # --------------------------------------------------
        # Case 3
        # --------------------------------------------------

        elif (not p1_loop) and p1_reached:
            if p2_reached:
                p1_icmp3 = 0
                p2_icmp3 = 0

                unreach_idx_p1 = None

                for i in range(len(hops_p1)):
                    if (
                        dest_unreach_p1[i]
                        and hops_p1[i] == ip
                    ):
                        if unreach_idx_p1 == None:
                            unreach_idx_p1 = i
                            p1_icmp3 = 1
                        else:
                            p1_icmp3+=1

                unreach_idx_p2 = None

                for i in range(len(hops_p2)):
                    if (
                        dest_unreach_p2[i]
                        and hops_p2[i] == ip
                    ):
                        if unreach_idx_p2 == None:
                            unreach_idx_p2 = i
                            p2_icmp3 = 1
                        else:
                            p2_icmp3+=1
                        
                # print("Hello there", unreach_idx_p1, unreach_idx_p2)
                ###########################################################
                if (unreach_idx_p1 is None or unreach_idx_p2 is None):
                    continue

                ratio = ratio = p2_icmp3 / p1_icmp3

                if ratio < 0.6:
                    likely_filtered.append(ip)

                    print("\nAccepted:", ip)

                    print(
                        "Reason: P2 has reduced ICMP3 count"
                    )

                    candidate_idx = None

                    for i in range(unreach_idx_p2 - 1, -1, -1):
                        if (hops_p2[i] != "*" and hops_p2[i] != ip):
                            candidate_idx = i
                            break

                    if candidate_idx is not None:
                        candidate_ip = hops_p2[candidate_idx]
                        if candidate_idx < len(hops_p1):

                            p1_same_ip = hops_p1[
                                candidate_idx
                            ]

                            # Exact Match
                            if p1_same_ip == candidate_ip:

                                asn = lookup_asn(
                                    candidate_ip,
                                    starts,
                                    intervals
                                )

                                if asn:

                                    print(
                                        "Middlebox detected:",
                                        candidate_ip,
                                        "ASN:",
                                        asn
                                    )

                                    detected_middleboxes.append(
                                        (
                                            ip,
                                            candidate_ip,
                                            asn
                                        )
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
                        print("\n Rejected as candidate IP not found")
                else:

                    print("\nRejected:", ip)

                    print(
                        "Reason: P2 ICMP11 still >=90% of P1"
                    )




                ############################################################
                if (unreach_idx_p1 - unreach_idx_p2) >1 :
                    likely_filtered.append(ip)
                    p1_candidate = hops_p1[
                        unreach_idx_p2 
                    ]

                    # Exact Match

                    if p1_candidate ==ip:
                        print("p1_same_candidate hop is equal to destination IP")
                        continue
                    elif p1_candidate == "*":
                        for i in range(len(hops_p2) - 1, -1, -1):
                            if (hops_p2[i] != "*" and hops_p2[i] != ip):

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

                        candidate_asn = lookup_asn(
                            p1_candidate,
                            starts,
                            intervals
                        )

                        dest_asn = lookup_asn(
                            ip,
                            starts,
                            intervals
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
                likely_filtered.append(ip)
                last_visible_idx = None

                last_visible_ip = None

                for i in range(len(hops_p2) - 1, -1, -1):
                    if (hops_p2[i] != "*" and hops_p2[i] != ip):

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

                if (
                    candidate_ip == "*"
                    or candidate_ip == ip
                ):
                    print(
                        "Middlebox not detected"
                    )

                    continue

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

                    detected_middleboxes.append(
                        (
                            ip,
                            candidate_ip,
                            candidate_asn
                        )
                    )

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

        for dst, middlebox_ip, asn in detected_middleboxes:

            f.write(f"{middlebox_ip}\n")

    # print("\n==========")
    # print("Destination IPs with matching ASN:")

    guessed_file = os.path.join(
        output_dir,
        f"{app}_guessed_asn.txt"
    )

    with open(guessed_file, "w") as f:

        for dst, asn in guessed_ases:

            f.write(f"{asn}\n")

    # print("\n==========")
    # print("Likely filtered destination IPs:")

    likely_file = os.path.join(
        output_dir,
        f"{app}_likely_filtered_dest_IP.txt"
    )

    with open(likely_file, "w") as f:

        for dst in likely_filtered:

            f.write(f"{dst}\n")

