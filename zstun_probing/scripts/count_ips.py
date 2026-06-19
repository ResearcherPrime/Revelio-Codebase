#!/usr/bin/env python3
import ipaddress
import sys

def union_ip_count(prefixes):
    # Compute exact count of unique IPs covered by prefixes (including network/broadcast)
    # by merging integer intervals (no full enumeration).
    intervals = []
    for p in prefixes:
        net = ipaddress.ip_network(p.strip())
        start = int(net.network_address)
        end = int(net.broadcast_address)
        intervals.append((start, end))
    if not intervals:
        return 0
    intervals.sort()
    merged = []
    cur_s, cur_e = intervals[0]
    for s, e in intervals[1:]:
        if s <= cur_e + 1:
            if e > cur_e:
                cur_e = e
        else:
            merged.append((cur_s, cur_e))
            cur_s, cur_e = s, e
    merged.append((cur_s, cur_e))
    total = sum(e - s + 1 for s, e in merged)
    return total

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <input_prefix_file>")
        sys.exit(1)

    input_file = sys.argv[1]

    with open(input_file, "r") as f:
        prefixes = [line.strip() for line in f if line.strip()]

    total = union_ip_count(prefixes)
    print(total)

if __name__ == "__main__":
    main()
