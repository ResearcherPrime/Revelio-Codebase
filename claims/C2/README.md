## Purpose of this directory
This folder contains config files and shell scripts which prepare the Rvelio codebase
such that it can run in the intended way to verify Claim - C2 as per artifact appendix

## Claim-C2
Revelio accurately detects VoIP censorship through differences in responses for vanilla
STUN, application-specific STUN, and modified application-specific STUN probes.

## Process followed for verifying the claim
1. Scrape the asn and then prefixes of a target country (e.g., the UAE) from the BGP and CIDR websites using `scraping` module
2. Probe the IP space of a target country (e.g., the UAE where WhatsApp is filtered) with vanilla STUN (P1), app-specific (WhatsApp) STUN (P2) and its modified version (P3) packets using `zstun_probing` module
3. Plot the graph for UDP, ICMP and No Response deviation to see the change in behaviour for different STUN probes using `zstun_probing_analysis` module
4. Compare the results from all three scans to prove the claim-C2 and pcaps related to it

### What is the conclusion?
- Using P1 probes we will understand that how does an IP behave for vanilla STUN packet:
(1) it responds with a STUN packet because it is a STUN server, (2) it responds with an
ICMP error because the destination is unreachable or time limit exceeded, (3) it will 
respond nothing because of how it was configured

- Now ideally P2 and P3 probes should behave the same way as the P1 probes assuming that
there exist no discrimination against these app-specific STUN packets. But as we have
reported that WhatsApp STUN packets face censorship (in the UAE), we will see the deviation
of responses for WhatsApp (P2) compared to P1 and P3 probes.

`Note: As this claim is being verified in the realtime over the internet, hence it is
possible that the censorship behavior may deviate from what was reported in the paper` 

## How to run the scripts?
Using `run_demo.sh` sets up the scan for verifying claim-C2 for United_Arab_Emirates (the 
entire IP space). 

## Expected run time
- `run_demo.sh` : 60 mins
- `run_comprehensive.sh` : 50 hours
