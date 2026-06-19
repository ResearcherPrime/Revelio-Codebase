import argparse

def get_args():

    parser = argparse.ArgumentParser(
        description="VoIP STUN traceroute"
    )

    parser.add_argument(
        "-dip",
        type=str,
        required=True,
        help="Destination IP"
    )

    parser.add_argument(
        "-sport",
        type=int,
        help="Source port"
    )

    parser.add_argument(
        "-dport",
        type=int,
        default=3478,
        help="Destination port"
    )

    parser.add_argument(
        "-pcap",
        type=int,
        help="PCAP replay index (-1 for vanilla STUN)"
    )

    parser.add_argument(
        "-app",
        type=str,
        choices=[
            "messenger",
            "signal",
            "telegram",
            "whatsapp"
        ],
        help="VoIP application replay profile"
    )

    parser.add_argument(
        "-tout",
        type=int,
        default=2,
        help="Timeout in seconds"
    )

    return parser.parse_args()

if __name__ == "__main__":

    args = get_args()

    print(args)
