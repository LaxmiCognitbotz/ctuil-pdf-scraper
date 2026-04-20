"""
Scraper for: https://ctuil.in/ists-consultation-meeting
Downloads PDFs from "Agenda" and "Minutes" columns for each region.
"""

import os
import re
import asyncio

import aiohttp
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

# ==== Config ====
BASE_URL = "https://ctuil.in/ists-consultation-meeting"
OUTPUT_DIR = "uploads/ists_consultation_meeting"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": BASE_URL,
}

REGIONS = [
    "Northern Region",
    "Western Region",
    "Southern Region",
    "Eastern Region",
    "North Eastern Region",
]

TAB_MAP = {
    "Northern Region": "1",
    "Western Region": "2",
    "Southern Region": "3",
    "Eastern Region": "4",
    "North Eastern Region": "5",
}

PAGE_SEM = asyncio.Semaphore(10)
DOWNLOAD_SEM = asyncio.Semaphore(20)


# ==== Utils ====
def safe_filename(url: str) -> str:
    name = unquote(url.split("/")[-1].split("?")[0])
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name.strip("._") or "file.pdf"

# ==== Fetch HTML ====
async def async_fetch(session, url):
    async with PAGE_SEM:
        async with session.get(url) as resp:
            return await resp.text()

# ==== Download File ====
async def async_download(session, url, dest):
    async with DOWNLOAD_SEM:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return
                data = await resp.read()

            os.makedirs(os.path.dirname(dest), exist_ok=True)

            with open(dest, "wb") as f:
                f.write(data)

            print(f"[OK] {dest}")

        except Exception as e:
            print("Download error:", e)

# ==== Extract Links ====
def extract_links(html: str, region_filter: str = None) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return {}

    header_row = table.find("tr")
    headers = [th.get_text(strip=True).lower()
               for th in header_row.find_all(["th", "td"])]

    col_map = {}
    for i, h in enumerate(headers):
        if h == "agenda":
            col_map["Agenda"] = i
        elif h in ("minutes", "mom"):
            col_map["Minutes"] = i

    col_map.setdefault("Agenda", 5)
    col_map.setdefault("Minutes", 6)

    region_map = {
        "Northern Region": "nr",
        "Western Region": "wr",
        "Southern Region": "sr",
        "Eastern Region": "er",
        "North Eastern Region": "ner",
    }

    target = region_map.get(region_filter, "").lower()

    results = {"Agenda": [], "Minutes": []}
    body_rows = table.find_all("tr")[1:]

    for row in body_rows:
        cells = row.find_all("td")

        for doc_type in ("Agenda", "Minutes"):
            col_idx = col_map.get(doc_type)
            if col_idx is None or col_idx >= len(cells):
                continue

            for a in cells[col_idx].find_all("a", href=True):
                href = a["href"].strip()
                if not href or href.startswith("#") or "javascript" in href:
                    continue

                full_url = href if href.startswith("http") else urljoin(BASE_URL, href)

                fname = full_url.lower()

                if target and f"cmets-{target}" not in fname:
                    continue

                results[doc_type].append(full_url)
    return results

# ==== Get total pages ====
def get_total_pages(html: str) -> int:
    m = re.search(r"Displaying\s+\d+\s+to\s+\d+\s+of\s+(\d+)", html, re.I)
    if m:
        total = int(m.group(1))
        return (total + 9) // 10
    return 1

# ==== Reorder Files (Shift Logic) ====
def reorder_files(dest_dir, urls):
    os.makedirs(dest_dir, exist_ok=True)

    # ==== Map existing files ====
    existing_map = {}
    for f in os.listdir(dest_dir):
        if "_" in f:
            original = f.split("_", 1)[1]
            existing_map[original] = f

    counter = 1

    for url in urls:
        original_name = safe_filename(url)
        new_name = f"{counter:02d}_{original_name}"
        new_path = os.path.join(dest_dir, new_name)

        if original_name in existing_map:
            old_path = os.path.join(dest_dir, existing_map[original_name])

            # ==== Rename existing file ====
            if old_path != new_path:
                os.rename(old_path, new_path)
        else:
            # ==== New file → Download ====
            yield (url, new_path)

        counter += 1

# ==== Scrape regions ====
async def scrape_region(session, region, tab_key):
    print(f"\n=== {region} ===")

    region_dir = os.path.join(OUTPUT_DIR, region.replace(" ", "_"))

    first_url = f"{BASE_URL}?p=ajax&page=1&tab={tab_key}"
    first_html = await async_fetch(session, first_url)
    total_pages = get_total_pages(first_html)

    # ==== Fetch all pages ====
    pages_html = []
    for page_num in range(1, total_pages + 1):
        url = f"{BASE_URL}?p=ajax&page={page_num}&tab={tab_key}"
        html = await async_fetch(session, url)
        pages_html.append(html)

    # ==== Collect Links ====
    collected = {"Agenda": [], "Minutes": []}

    for html in pages_html:
        links = extract_links(html, region_filter=region)
        for doc_type in collected:
            collected[doc_type].extend(links.get(doc_type, []))

    # ==== Reorder + Download ====
    download_tasks = []

    for doc_type in ("Agenda", "Minutes"):
        urls = collected[doc_type]
        dest_dir = os.path.join(region_dir, doc_type)

        for url, dest in reorder_files(dest_dir, urls):
            download_tasks.append(
                async_download(session, url, dest)
            )
    await asyncio.gather(*download_tasks)


# ==== Main ====
async def main():
    async with aiohttp.ClientSession(headers=HEADERS) as session:

        tasks = [
            scrape_region(session, region, TAB_MAP[region])
            for region in REGIONS
        ]

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())