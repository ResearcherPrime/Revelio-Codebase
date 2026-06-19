#!/usr/bin/env python3

import secrets
import os
import signal
import copy

from datetime import datetime

from scapy.all import *
from scapy.utils import rdpcap
from scapy.contrib.stun import STUN, STUNGenericTlv

from utils import arg_parser as parser
from utils import constants as const

args = parser.get_args()

# ==================================================
# Arguments
# ==================================================

target_ip = args.dip

sport = (
    RandShort()._fix()
    if args.sport is None
    else args.sport
)

dport = args.dport

timeout = args.tout

max_ttl = 30

# ==================================================
# Resolve replay mode
# ==================================================

if args.app is not None:

    if args.app not in const.APP_PCAP_MAP:

        raise ValueError(
            f"Unsupported app: {args.app}"
        )

    pcap_path = const.APP_PCAP_MAP[args.app]

    pkt_idx = 0

    replay_mode = "app"

else:

    replay_mode = "vanilla"

# ==================================================
# Banner
# ==================================================

print(f"\n=== STUN traceroute to {target_ip} ===\n")

# ==================================================
# Formatting helper
# ==================================================

def fmt(ttl, kind, outer, inner_src, inner_dst):

    return (
        f"{ttl:>2} | "
        f"{kind:<20} | "
        f"outer= {outer:<15} | "
        f"inner= {inner_src:<15} -> {inner_dst:<15}"
    )

# ==================================================
# Build STUN packet template
# ==================================================

if replay_mode == "vanilla":

    t_id = int(secrets.token_hex(12), 16)

    msg_type = 0x0003

    attributes = [
        STUNGenericTlv(
            type=0x0019,
            length=4,
            value=b'\x11\x00\x00\x00'
        )
    ]

else:

    pkt = rdpcap(pcap_path)[pkt_idx]

    try:

        stun_layer = pkt[IP][UDP][STUN]

    except:

        stun_layer = STUN(
            bytes(pkt[UDP].payload)
        )

    t_id = stun_layer.transaction_id

    msg_type = stun_layer.stun_message_type

    attributes = copy.deepcopy(
        stun_layer.attributes
    )

# ==================================================
# PCAP capture setup
# ==================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURE_DIR = os.path.join(BASE_DIR, "trace_pcap_captures")

os.makedirs(CAPTURE_DIR, exist_ok=True)

sniffer = None

pcap_out = None

def start_capture(target_ip, dport):

    flt = (
        f"host {target_ip} "
        f"or (udp port {dport} or icmp)"
    )

    s = AsyncSniffer(
        filter=flt,
        store=True
    )

    s.start()

    return s

# ==================================================
# SIGTSTP handler
# ==================================================

def handle_sigtstp(sig, frame):

    global sniffer, pcap_out

    print("\n[!] SIGTSTP received, flushing PCAP")

    try:

        if sniffer is not None:

            pkts = sniffer.stop()

            if pkts:

                wrpcap(pcap_out, pkts)

                print(f"[+] PCAP saved: {pcap_out}")

    except Exception as e:

        print(f"[!] Error while saving PCAP: {e}")

    os.kill(os.getpid(), signal.SIGSTOP)

signal.signal(signal.SIGTSTP, handle_sigtstp)

# ==================================================
# Start capture
# ==================================================

ts = datetime.utcnow().strftime(
    "%Y%m%d_%H%M%S"
)

trace_name = (
    args.app
    if args.app is not None
    else "vanilla"
)

pcap_out = (
    f"{CAPTURE_DIR}/"
    f"{target_ip}_"
    f"{trace_name}_"
    f"{ts}.pcap"
)

sniffer = start_capture(target_ip, dport)

# ==================================================
# Traceroute loop
# ==================================================

try:

    for ttl in range(max_ttl + 1):

        ip = IP(
            dst=target_ip,
            ttl=ttl
        )

        udp = UDP(
            sport=sport,
            dport=dport
        )

        stun = STUN(
            transaction_id=t_id,
            stun_message_type=msg_type,
            attributes=attributes
        )

        pkt = ip / udp / stun

        reply = sr1(
            pkt,
            timeout=timeout,
            verbose=False
        )

        if reply is None:

            print(
                fmt(
                    ttl,
                    "*",
                    "NA",
                    "NA",
                    "NA"
                )
            )

            continue

        # ==================================================
        # ICMP response
        # ==================================================

        if reply.haslayer(ICMP):

            icmp = reply[ICMP]

            outer_ip = reply[IP].src

            inner_src = inner_dst = "NA"

            try:

                quoted = IP(bytes(icmp.payload))

                inner_src = quoted.src

                inner_dst = quoted.dst

            except:

                pass

            print(
                fmt(
                    ttl,
                    f"ICMP t={icmp.type} c={icmp.code}",
                    outer_ip,
                    inner_src,
                    inner_dst
                )
            )

        # ==================================================
        # Non-ICMP response
        # ==================================================

        else:

            proto = (
                reply.payload.__class__.__name__
            )

            print(
                fmt(
                    ttl,
                    f"NON-ICMP {proto}",
                    reply[IP].src,
                    "NA",
                    "NA"
                )
            )

finally:

    if sniffer is not None:

        pkts = sniffer.stop()

        if pkts:

            wrpcap(pcap_out, pkts)

            print(f"[+] PCAP saved: {pcap_out}")
