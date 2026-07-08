# ZSTUN Probing

## Purpose
This module is used for performing Zstun scans with vanilla and voip app specific STUN packets. We later use the output of these scans to decide how does an IP behave across different STUN packet probes:
- Responsive (UDP)
- ICMP Errors (TTL expire, Port/Dest Unreachable, Others)
- Misc Response
- No Response

## Installation
- sudo apt-get install build-essential cmake libgmp3-dev gengetopt libpcap-dev flex byacc libjson-c-dev pkg-config libunistring-dev libjudy-dev unzip
- unzip modified_zmap.zip
- cd zmap-4.3.4
- rm -r build
- mkdir build; cd build
- cmake .. -DCMAKE\_INSTALL\_PREFIX=/usr
- make -j$(nproc)
- make install

## Misc 
How does balance_groups function in launcher works?

Distributes country CSV files into 4 groups so that each group has roughly the same total number of IPs (line counts).

Input: input.csv   → contains one filename per line (e.g., US.csv, IN.csv)

Arguments: $1 = prefix path (e.g., /opt/countries)

Outputs: group0.txt ... group7.txt (with prefix applied). It returns plain filenames grouped, separated by "|"
