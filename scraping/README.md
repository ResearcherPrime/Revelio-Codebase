# Scraping

## Purpose
This module is required to generate the input prefixes for Zstun scans next. First of all the asns_scrapper.py is going to scrape countries with their original names from the bgp.he.net website and then the respective asn names also will be fetched individual country. Then for each asn prefixes are fetched from the CIDR report.

## Installation
- `pip install beautifulsoup4` (version - beautifulsoup4-4.13.4) has to be done for the script to run.
- `apt install tmux` needed to run multiple instance of scripts automatically

## Country Scraping
- Target website -> https://bgp.he.net/report/world 
- Total countries scrapped -> 241
- Filename - countries.csv (Country Name, Country Code, Report Link)

## ASNs scraping (per country)
- Target website -> https://bgp.he.net/country/{country\_code}
- Filename - /asns/{country\_name}.csv (ASN, Name)
- One country with code "AP" has no name and no ASNs listed over website
- "United Kingdom" & "Netherlands Antillies" have no ASNs listed over website

## IP Prefix scraping (per ASN)
- Target website -> https://www.cidr-report.org/cgi-bin/as-report?as={as\_no}&view=2.0
- Filename - /prefixes/{country\_name}.csv (ASN, Prefix)
- Will scrape them individually on demand using ASNs files (for eg. asns/Mayanmar.csv)
- Can use batch\_prefix\_scraper.sh over an input text file (for eg. middle\_east\_countries.txt) or all countries unders asns (default behaviour)

## Possible Errors and Resolution
It may so happen that due to continuous web-scraping sometimes the websites like Hurricane Electric or CIDR report will deny the incoming get requests.
```
Error - HTTPSConnectionPool(host='bgp.he.net', port=443): Max retries exceeded with url: /country/MX (Caused by NewConnectionError('<urllib3.connection.HTTPSConnection object at 0x7f651989bd90>: Failed to establish a new connection: [Errno 101] Network is unreachable'))
```

Precaution Taken - We keep a sleep time of 2 second between contiguous requests to avoid this error.

Resolution - Restart the scans after killing the previous tmux sessions (`tmux kill-server`).
