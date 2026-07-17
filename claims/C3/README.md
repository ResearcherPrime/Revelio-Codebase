## Purpose of this directory
This folder contains config files and shell scripts which prepare the Rvelio codebase
such that it can run in the intended way to verify Claim - C3 as per artifact appendix

## Claim-C3
Revelio accurately detects VoIP censorship through differential analysis of vanilla STUN,
application-specific STUN, and modified application-specific STUN probes.

## Process followed for verifying the claim
1. Scrape the asn and then prefixes of a target country (e.g., the UAE) from the BGP and CIDR websites using `scraping` module
2. Probe the IP space of a target country (e.g., the UAE) with vanilla STUN (P1), app-specific (WhatsApp) STUN (P2) and its modified version (P3) packets using `zstun_probing` module
3. Find the IPs along whose path we encounter any kind of deviation in response behaviour for different STUN probes. Use `zstun_probing_analysis` module for this.
4. Using `stun_trace` module launch traceroutes (using P1 and P2 pakctes) to these filtered destinations.
5. Try to classify filtering behaviour and pinpoint the middlebox location to prove the claim-C3

### What is the conclusion?
- Using P1 packets for traceroute will give us the probable hops that would be encountered
while probing these filtered destinations from our scanning machines that can serve as the
baseline to be compared with hops encountered using P2 packets

- Due to the traceroutes being targetted to the filtered destination IPs we would be able
to observe which particular hop is responsible for the deviation seen via P2 packets and
thus we would be able to conclude if we can classify middlebox behaviour and location.

`Note: As this claim is being verified in the realtime over the internet, hence it is
possible that some middlebox behaviours are not encountered due to the evolving censorship` 

## How to run the scripts?
Using `run_demo.sh` sets up the scan for verifying claim-C3 for a small set of prefixes
from United_Arab_Emirates along whose path we detected the presence of filtering due to
a middlebox. The `run_comprehensive.sh` script verifies the same thing for the all 
filtered destinations identified during the scan of entire United_Arab_Emirates and 
thus take more time than former one.

## Expected run time
- `run_demo.sh` : 1 hour 40 mins
- `run_comprehensive.sh` : 30 hours
