import os

# --------------------------------------------------
# Base paths
# --------------------------------------------------

SCRIPT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_ROOT = os.path.dirname(
    SCRIPT_DIR
)

PCAP_DIR = os.path.join(
    PROJECT_ROOT,
    "pcaps"
)

# --------------------------------------------------
# PCAP mappings
# --------------------------------------------------

APP_PCAP_MAP = {
    "messenger": os.path.join(
        PCAP_DIR,
        "Messenger_Allocate_User.pcap"
    ),

    "signal": os.path.join(
        PCAP_DIR,
        "Signal_Allocate_User.pcap"
    ),

    "telegram": os.path.join(
        PCAP_DIR,
        "Telegram_Allocate_User.pcap"
    ),

    "whatsapp": os.path.join(
        PCAP_DIR,
        "Whatsapp_Allocate_Voice.pcap"
    ),
}

# --------------------------------------------------
# Output files
# --------------------------------------------------

summaryfile = "summary.txt"

dumpfile = "dump.txt"

replyingipsfile = "rips.csv"

nonreplyingipsfile = "nrips.csv"

# --------------------------------------------------
# Timeouts
# --------------------------------------------------

tout_short = 2

tout_long = 5

# --------------------------------------------------
# Separators
# --------------------------------------------------

ip_separator = (
    "\n-------------------------------------------------"
    "IP Separator"
    "-------------------------------------------------\n"
)

pkt_separator = (
    "\n-------------------------------------------------"
    "Pkt Separator"
    "-------------------------------------------------\n"
)
