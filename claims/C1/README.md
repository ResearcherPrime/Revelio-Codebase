## Purpose of this directory
This folder contains config files and shell scripts which prepare the Rvelio codebase
such that it can run in the intended way to verify Claim - C1 as per artifact appendix

## Claim-C1
Zstun discovers usable STUN infrastructure that cannot be reliably identified using
standard Internet-wide scanning approaches.

## Process followed for verifying the claim
1. Scrape the asn and then prefixes of a country from the BGP and CIDR websites using `scraping` module
2. Perform port scan for UDP 3478 & TCP 3478 on the entire IP space of the country using `port_scanning` module
3. Probe the IP space a country with vanilla STUN packets to get actual STUN servers using `zstun_probing` module
4. Compare the results from all three scans to prove the claim-C1

### What is the conclusion?
- Using UDP 3478 port scan it is proved that very minimal amount of STUN servers respond
to the generic UDP probe packets thus not discoverable by this port scan

- Using TCP 3478 scan it is proved that there a lot more IPs that will respond to TCP SYN
packets but they are not confirmed STUN servers and many of them might be false positives

- Using Zstun vanilla scan it is proved that there are actually a lot of STUN servers that
were not discovered earlier but it also does not contain any false psotive becuase each IP
probed has responded with some kind of valid STUN reponse

## How to run the scripts?
Using `run_demo.sh` sets up the scan for verifying claim-C1 for United_Arab_Emirates and
thus it completes relatively faster than `run_comprehensive.sh` which verifies the same
thing for all the 19 countries that which were reported to do VoIP filtering.

## Expected run time
- `run_demo.sh` : 5 mins (to be verified)
- `run_comprehensive.sh` : 1 hour (to be verified)
