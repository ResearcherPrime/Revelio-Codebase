import requests
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

ASNS_DIR = os.path.join(
    SCRIPT_DIR,
    "asns"
)

os.makedirs(ASNS_DIR, exist_ok=True)

os.makedirs(EXEC_LOG_DIR, exist_ok=True)

os.makedirs(TIME_LOG_DIR, exist_ok=True)

log = open(
    os.path.join(
        EXEC_LOG_DIR,
        "asns_scraper.txt"
    ),
    "w",
    buffering=1
)

time_log = open(
    os.path.join(
        TIME_LOG_DIR,
        "asns_scraper.txt"
    ),
    "w",
    buffering=1
)

TARGET_COUNTRY = None

if len(sys.argv) > 1:
    TARGET_COUNTRY = sys.argv[1].strip().lower()


def scrape_countries(url):
    log.write("Country list scrapping started\n\n")

    response = requests.get(url, timeout=30)

    triplets = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find('table', id="table_countries")

        if table:
            rows = table.find_all('tr')

            if rows:
                for row in rows[1:]:

                    cells = row.find_all('td')

                    if cells:
                        name = "".join(
                            cells[0]
                            .find('div', class_="down2 floatleft")
                            .text
                            .strip()
                        )

                        code = "".join(cells[1].text.strip())

                        link = (
                            "https://bgp.he.net"
                            + cells[3].find('a').attrs['href'].strip()
                        )

                        triplets.append((name, code, link))

                    else:
                        log.write("No <td> tags found in the table row\n")
                        log.write(str(row))

            else:
                log.write("No <tr> tags found after table tag\n")

        else:
            log.write("Table with table_countries id not found\n")

    else:
        log.write(
            f"Error: Unable to fetch page, status code {response.status_code}\n"
        )

    log.write("Country list scrapping ended\n\n")

    return triplets


def scrape_asns(country, url):

    log.write(f"ASNs list scrapping for {country} started\n\n")

    response = requests.get(url, timeout=30)

    asns = []

    if response.status_code == 200:

        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find('table', id="asns")

        if table:

            rows = table.find_all('tr')

            if rows:

                for row in rows[1:]:

                    cells = row.find_all('td')

                    if cells:

                        asn = "".join(
                            cells[0]
                            .find('a')
                            .text
                            .strip()
                        )

                        name = "".join(cells[1].text.strip())

                        asns.append((asn, name))

                    else:
                        log.write("No <td> tags found in the table row.\n")
                        log.write(str(row))

            else:
                log.write("No <tr> tags found after table tag\n")

        else:
            log.write("Table with asns id not found\n")

    else:
        log.write(
            f"Error: Unable to fetch page, status code {response.status_code}\n"
        )

    log.write(f"ASNs list scrapping for {country} ended\n\n")

    return asns


def main():

    try:

        start = time.time()

        url = "https://bgp.he.net/report/world"

        triplets = scrape_countries(url)

        file_name = os.path.join(
            SCRIPT_DIR,
            "bgp_world_report.csv"
        )

        with open(file_name, mode="w", newline="") as file:

            writer = csv.writer(file)

            writer.writerow([
                "Country Name",
                "Country Code",
                "Report Link"
            ])

            writer.writerows(triplets)

        names = set()

        for entry in triplets:

            country_name = entry[0]

            if TARGET_COUNTRY is not None:
                if country_name.strip().lower() != TARGET_COUNTRY:
                    continue

            country_start = time.time()

            asns = scrape_asns(entry[0], entry[2])

            file_name = (
                entry[0]
                .replace(",", "")
                .replace(".", "")
                .replace(" ", "_")
            )

            if file_name in names:
                file_name = f"{file_name}_{entry[1]}"

            names.add(file_name)

            file_name = os.path.join(
                ASNS_DIR,
                f"{file_name}.csv"
            )
            with open(file_name, mode="w", newline="") as file:

                writer = csv.writer(file)

                writer.writerow(["ASN", "Name"])

                asns.sort()

                writer.writerows(asns)

                print(file_name)

            country_end = time.time()

            time_log.write(
                f"{entry[0]}: "
                f"{country_end - country_start:.2f} seconds\n"
            )

            if TARGET_COUNTRY is None:
                time.sleep(1)

        end = time.time()

        elapsed = end - start

        mins, secs = divmod(int(elapsed), 60)
        hours, mins = divmod(mins, 60)

        time_log.write(
            f"\nTotal Time: {hours}h {mins}m {secs}s\n"
        )

        time_log.close()
        log.close()

        return 0

    except Exception as e:

        if log is not None:
            log.write(str(e))
            log.write("\n")
            log.write("ASNs list scrapping ended\n\n")

        print(e)

        return 1


if __name__ == "__main__":

    code = main()

    sys.exit(code)
