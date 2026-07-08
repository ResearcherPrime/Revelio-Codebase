# Stun Trace

## Purpose 
The module compares traceroute behavior between `vanilla STUN traffic` and `replayed VoIP STUN traffic` to infer where filtering or traffic manipulation may occur along the network path.

The `stun_trace` module performs STUN packet-based traceroutes to identify:
- possible filtering middleboxes
- dropping of censored packets
- ASN-level filtering inference
- likely filtered locations

## Installation
`pip install scapy` - to be able to craft stun packets for traceroute

