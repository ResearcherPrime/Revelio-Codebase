## Purpose
This module is used for performing port scanning and dividing the IPs into separate categories like:
- Responsive (UDP, Synack)
- ICMP Errors (TTL expire, Port/Dest Unreachable, Others)
- Misc Response
- No Response

## Installation
- sudo apt-get install build-essential cmake libgmp3-dev gengetopt libpcap-dev flex byacc libjson-c-dev pkg-config libunistring-dev libjudy-dev
- unzip modified_zmap.zip
- cd zmap-4.3.4
- mkdir build; cd build
- cmake .. -DCMAKE\_INSTALL\_PREFIX=/usr
- make -j$(nproc)
- make install
