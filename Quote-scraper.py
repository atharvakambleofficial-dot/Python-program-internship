#!/usr/bin/env python3
"""
Quote Scraper
=============
Fetch pages from quotes.toscrape.com (a website built for scraping practice),
pick out each quote with BeautifulSoup, and save the results as clean JSON
and plain text.

Install the two libraries once:
    pip install requests beautifulsoup4

Run:
    python quote_scraper.py                 # first 3 pages (30 quotes)
    python quote_scraper.py --pages 10      # all 10 pages (100 quotes)
    python quote_scraper.py --delay 2       # wait 2 seconds between requests

Polite and legal scraping, built in
-----------------------------------
* Only a public practice site is scraped: no login, no personal data.
* robots.txt is checked before any page is requested.
* The program identifies itself with a User-Agent header.
* It waits between requests (never less than MIN_DELAY seconds).
* It stops at the first error instead of retrying aggressively.
* It never follows a "next page" link that leaves the site.

If the site layout changes, only the SELECTORS dictionary needs fixing.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Missing libraries. Install them with:\n  pip install requests beautifulsoup4")

# ----------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------
BASE_URL = "https://quotes.toscrape.com"
START_URL = BASE_URL + "/"
USER_AGENT = "QuoteScraperStudentProject/1.0 (learning exercise)"

REQUEST_TIMEOUT = 10        # seconds to wait for the server
DEFAULT_PAGES = 3           # 10 quotes per page
MAX_PAGES_ALLOWED = 10      # the site only has 10 pages
DEFAULT_DELAY = 1.0         # seconds between requests
MIN_DELAY = 0.5             # never go faster than this

OUTPUT_DIR = Path(__file__).resolve().parent
JSON_FILE = OUTPUT_DIR / "quotes.json"
TEXT_FILE = OUTPUT_DIR / "quotes.txt"

QUOTE_MARKS = "\u201c\u201d\" "  # curly/straight double quotes and spaces

# All CSS selectors live here, so they are easy to fix if the site changes.
SELECTORS = {
    "quote_block": "div.quote",
    "text": "span.text",
    "author": "small.author",
    "tags": "div.tags a.tag",
    "next_page": "li.next > a",
}


# ----------------------------------------------------------------------
# Step 1: HTTP requests
# ----------------------------------------------------------------------
def load_robots(session):
    """Download and parse robots.txt. Returns a parser, or None to stop."""
    robots_url = urljoin(BASE_URL, "/robots.txt")
    parser = RobotFileParser()

    try:
        response = session.get(robots_url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as err:
        print(f"Could not download robots.txt ({err}). Stopping to be safe.")
        return None

    if response.status_code == 200:
        parser.parse(response.text.splitlines())
    elif 400 <= response.status_code < 500:
        parser.parse([])  # no robots.txt means no restrictions
        print(f"No robots.txt found (HTTP {response.status_code}): no restrictions to follow.")
    else:
        print(f"robots.txt returned HTTP {response.status_code}. Stopping to be safe.")
        return None
    return parser


def fetch_page(session, url):
    """Download one page and return a BeautifulSoup object (None on error)."""
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.Timeout:
        print(f"  Error: the request timed out for {url}")
    except requests.ConnectionError:
        print("  Error: could not connect. Check your internet connection.")
    except requests.HTTPError as err:
        code = err.response.status_code
        if code == 429:
            print("  Error: the server says we are going too fast (HTTP 429). Try a larger --delay.")
        else:
            print(f"  Error: the server returned HTTP {code} for {url}")
    except requests.RequestException as err:
        print(f"  Error: the request failed ({err})")
    else:
        # Pass raw bytes so BeautifulSoup works out the text encoding itself.
        return BeautifulSoup(response.content, "html.parser")
    return None


# ----------------------------------------------------------------------
# Step 2: HTML extraction
# ----------------------------------------------------------------------
def clean_text(text):
    """Collapse tabs, newlines and repeated spaces into single spaces."""
    return " ".join(text.split())


def text_of(parent, selector):
    """Text of the first element matching selector, or None if it is missing."""
    element = parent.select_one(selector)
    if element is None:  # check for None BEFORE calling get_text()
        return None
    return clean_text(element.get_text())


def parse_quotes(soup, page_number):
    """Turn one page of HTML into a list of clean quote dictionaries."""
    records = []
    for block in soup.select(SELECTORS["quote_block"]):
        text = text_of(block, SELECTORS["text"])
        author = text_of(block, SELECTORS["author"])
        if not text or not author:
            print("  Warning: skipped a quote block with missing text or author.")
            continue

        tags = [clean_text(tag.get_text()) for tag in block.select(SELECTORS["tags"])]
        records.append({
            "text": text.strip(QUOTE_MARKS),
            "author": author,
            "tags": [tag for tag in tags if tag],
            "page": page_number,
        })
    return records


def find_next_url(soup, current_url):
    """Return the URL of the next page, or None if this is the last one."""
    link = soup.select_one(SELECTORS["next_page"])
    if link is None or not link.get("href"):
        return None

    next_url = urljoin(current_url, link["href"])
    if urlparse(next_url).netloc != urlparse(BASE_URL).netloc:
        print("  The next-page link leaves the site, so it is ignored.")
        return None
    return next_url


# ----------------------------------------------------------------------
# Step 3: Put it together (politely)
# ----------------------------------------------------------------------
def scrape(max_pages, delay):
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    robots = load_robots(session)
    if robots is None:
        return []

    records = []
    visited = set()
    url = START_URL
    pages_done = 0

    try:
        while url and pages_done < max_pages:
            if url in visited:  # guards against a "next" link that loops back
                break
            visited.add(url)

            if not robots.can_fetch(USER_AGENT, url):
                print(f"robots.txt does not allow {url}. Stopping.")
                break

            time.sleep(delay)  # polite pause before every page request
            pages_done += 1
            print(f"Page {pages_done}: {url}")

            soup = fetch_page(session, url)
            if soup is None:
                break

            found = parse_quotes(soup, pages_done)
            print(f"  found {len(found)} quote(s)")
            if not found and pages_done == 1:
                print("  No quotes found. The site layout may have changed: check SELECTORS.")
            records.extend(found)

            url = find_next_url(soup, url)
    except KeyboardInterrupt:
        print("\nStopped by you. Saving what was collected so far.")

    return records


# ----------------------------------------------------------------------
# Step 4: Save as clean JSON / text
# ----------------------------------------------------------------------
def save_json(records, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
        f.write("\n")


def save_text(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for number, record in enumerate(records, start=1):
            f.write(f'{number}. "{record["text"]}"\n')
            f.write(f'   - {record["author"]}\n')
            if record["tags"]:
                f.write(f'   Tags: {", ".join(record["tags"])}\n')
            f.write("\n")


def main():
    arg_parser = argparse.ArgumentParser(description="Scrape quotes from quotes.toscrape.com")
    arg_parser.add_argument("--pages", type=int, default=DEFAULT_PAGES,
                            help=f"pages to scrape, 1-{MAX_PAGES_ALLOWED} (default {DEFAULT_PAGES})")
    arg_parser.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                            help=f"seconds between requests (default {DEFAULT_DELAY}, minimum {MIN_DELAY})")
    args = arg_parser.parse_args()

    pages = min(max(args.pages, 1), MAX_PAGES_ALLOWED)
    delay = max(args.delay, MIN_DELAY)
    if pages != args.pages:
        print(f"Pages must be between 1 and {MAX_PAGES_ALLOWED}; using {pages}.")
    if delay != args.delay:
        print(f"Delay raised to the minimum of {MIN_DELAY} seconds to be polite.")

    print(f"Scraping up to {pages} page(s) from {BASE_URL} ...\n")
    records = scrape(pages, delay)

    if not records:
        print("\nNo quotes were collected, so no files were written.")
        return

    try:
        save_json(records, JSON_FILE)
        save_text(records, TEXT_FILE)
    except OSError as err:
        print(f"\nCould not save the files: {err}")
        return

    authors = {record["author"] for record in records}
    print(f"\nDone! {len(records)} quote(s) from {len(authors)} author(s).")
    print(f"Saved: {JSON_FILE.name} and {TEXT_FILE.name} in {OUTPUT_DIR}")

    print("\nPreview:")
    for record in records[:2]:
        print(f'  "{record["text"][:70]}..." - {record["author"]}')


if __name__ == "__main__":
    main()