import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import csv
import time
import sys
import os

SCRIPT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

EXEC_LOG_DIR = os.path.join(
    SCRIPT_DIR,
    "logs",
    "exec"
)

TIME_LOG_DIR = os.path.join(
    SCRIPT_DIR,
    "logs",
    "time"
)

PREFIXES_DIR = os.path.join(
    SCRIPT_DIR,
    "prefixes"
)

os.makedirs(EXEC_LOG_DIR, exist_ok=True)

os.makedirs(TIME_LOG_DIR, exist_ok=True)

os.makedirs(PREFIXES_DIR, exist_ok=True)

log = None
time_log = None

# Note: Keep check if the BGP website change their country names
name_mapping = {
    'Korea_Republic_of': 'South_Korea',
    'Viet_Nam': 'Vietnam',
    'Venezuela_Bolivarian_Republic_of': 'Venezuela',
    'Iran_Islamic_Republic_of': 'Iran',
    'Russian_Federation': 'Russia',
}

# Default waiting time between consecutive CIDR requests
# Reduced during fast runs to speed up artifact evaluation
REQUEST_SLEEP_SECONDS = 8


def scrape(url):

    ip_set = set()

    try:
        response = requests.get(url, timeout=60)
    except RequestException as e:
        log.write(f"Request failed: {url} : {e}\n")
        return []

    if response.status_code == 200:

        soup = BeautifulSoup(response.text, 'html.parser')

        header = soup.find('h3', string="Announced Prefixes")

        if header:

            # Access the next sibling tags
            ul = header.find_next('ul')

            if ul:

                pre_tags = soup.find_all('pre')

                # Search for the pre tag containing the exact phrase
                # "AS Path" that comes before "Total Advertisements"

                for pre in pre_tags:

                    if "AS Path" in pre.text:

                        green_ips = pre.find_all('a', class_='green')
                        black_ips = pre.find_all('a', class_='black')

                        for ip in green_ips:
                            ip_set.add(ip.text)

                        for ip in black_ips:
                            ip_set.add(ip.text)

                        break

            else:
                log.write("No ul tag found after header paragraph\n")

        else:
            log.write("Paragraph with target header text not found\n")

    else:
        log.write(
            f"Error: Unable to fetch page, "
            f"status code {response.status_code}\n"
        )

    return list(ip_set)


def main():

    try:

        if len(sys.argv) <= 2:
            print(
                "Usage: "
                "<country_asns_list> "
                "<log_file_name> "
                "<offset> "
                "[fast_run]"
            )
            return 1

        start = time.time()

        global log
        global time_log
        global REQUEST_SLEEP_SECONDS

        # Optional fast-run optimization
        # Example:
        # python3 prefix_scrapper.py UAE fast 0 fast

        FAST_RUN = False

        if len(sys.argv) > 4:
            if sys.argv[4].lower() == "fast":
                FAST_RUN = True
                REQUEST_SLEEP_SECONDS = 2

        log_name = sys.argv[2]

        log = open(
            os.path.join(
                EXEC_LOG_DIR,
                f"prefix_scraping_{log_name}.log"
            ),
            "a",
            buffering=1
        )

        time_log = open(
            os.path.join(
                TIME_LOG_DIR,
                f"prefix_scraping_{log_name}.log"
            ),
            "a",
            buffering=1
        )

        asns = list()

        csv_file = f"{sys.argv[1]}.csv"

        country = sys.argv[1].split("/")[-1]

        if country in name_mapping:
            country = name_mapping[country]

        log.write(f"Prefix list scraping for {country} started\n\n")

        if FAST_RUN:
            log.write(
                "Fast run enabled "
                "(reduced inter-request delay)\n\n"
            )

        with open(csv_file, mode="r") as file:

            reader = csv.reader(file)

            next(reader)

            for row in reader:
                asns.append(row[0])

        offset = int(sys.argv[3])

        # Time offset to avoid overloading the CIDR website
        # while scraping from multiple parallel processes

        time.sleep(offset)

        prefixes = []

        for asn in asns:

            url = (
                "https://www.cidr-report.org/"
                f"cgi-bin/as-report?as={asn}&view=2.0"
            )

            ips = scrape(url)

            ips.sort()

            log.write(f"{asn} - {len(ips)}\n")

            temp = [(asn, ip) for ip in ips]

            prefixes.extend(temp)

            # Waiting time between multiple scraping requests
            # sent by each scraping process

            time.sleep(REQUEST_SLEEP_SECONDS)

        file_name = os.path.join(
            PREFIXES_DIR,
            f"{country}.csv"
        )

        with open(file_name, mode="w", newline="") as file:

            writer = csv.writer(file)

            writer.writerow(["ASN", "Prefix"])

            writer.writerows(prefixes)

        end = time.time()

        elapsed = end - start

        mins, secs = divmod(int(elapsed), 60)
        hours, mins = divmod(mins, 60)

        time_log.write(
            f"\n{country}: {hours}h {mins}m {secs}s\n"
        )

        log.write(
            f"Prefix list scraping for {country} ended\n\n"
        )

        time_log.close()
        log.close()

        return 0

    except Exception as e:

        if log is not None:
            log.write(str(e))
            log.write("\n")
            log.write(
                f"Prefix list scraping for {country} ended\n\n"
            )

        print(e)

        return 1


if __name__ == "__main__":

    code = main()

    sys.exit(code)
