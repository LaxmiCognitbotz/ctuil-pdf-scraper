"""
Scraper for: https://ctuil.in/regenerators
Downloads PDFs from "Effective date of connectivity wise" column, and renames them with month prefix.
"""

import os
import re
import asyncio

import aiohttp
from urllib.parse import unquote
from bs4 import BeautifulSoup

PAGE_URL   = "https://ctuil.in/regenerators"
BASE_URL   = "https://ctuil.in"
TARGET_DIR = "uploads/Effective_Date_Wise"

DOWNLOAD_SEM = asyncio.Semaphore(10)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": PAGE_URL,
}


def safe_filename(url: str) -> str:
    name = unquote(url.split("/")[-1].split("?")[0])
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name.strip("._") or "file.pdf"

def safe_month(raw: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f\s]', "_", raw.strip())

def make_display_name(month: str, url: str) -> str:
    return f"{month}_{safe_filename(url)}"

# ==== Fetch Page ====
async def fetch_rendered_html() -> str:
    from playwright.async_api import async_playwright

    print("Launching headless browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Use domcontentloaded — site never reaches networkidle
        await page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=30000)

        # Wait for table with PDF links to appear
        await page.wait_for_selector("table a[href]", timeout=15000)

        html = await page.content()
        await browser.close()

    print("Page rendered.\n")
    return html


# ==== Extract Links ====
def extract_links(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        print("[WARN] No table found.")
        return []

    header_row = table.find("tr")
    headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
    print(f"Headers: {headers}")

    # Auto-detect "Effective date of connectivity wise" column
    col_idx = 2
    for i, h in enumerate(headers):
        if "effective date" in h.lower() and "wise" in h.lower():
            col_idx = i
            break
    print(f"Target column: {col_idx} → '{headers[col_idx] if col_idx < len(headers) else '?'}'\n")

    results = []
    for tr in table.find_all("tr")[1:]:
        cells = tr.find_all("td")
        if not cells:
            continue

        month = safe_month(cells[0].get_text(strip=True)) if cells else "Unknown"

        if col_idx >= len(cells):
            continue

        for a in cells[col_idx].find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("#") or "javascript" in href:
                continue
            full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            results.append((month, full_url))

    return results

# ==== Download ====
async def async_download(session, url: str, dest: str):
    async with DOWNLOAD_SEM:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    print(f"[SKIP {resp.status}] {url}")
                    return
                data = await resp.read()

            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
            print(f"[DOWNLOADED] {dest}")

        except Exception as e:
            print(f"[ERROR] {url} → {e}")

# ==== Reorder + Plan ====
def reorder_and_plan(dest_dir: str, ordered_links: list) -> list:
    os.makedirs(dest_dir, exist_ok=True)

    # Map display_name → current filename on disk (strip number prefix)
    existing_map = {}
    for fname in os.listdir(dest_dir):
        if not os.path.isfile(os.path.join(dest_dir, fname)):
            continue
        parts = fname.split("_", 1)
        display_name = parts[1] if len(parts) == 2 and parts[0].isdigit() else fname
        existing_map[display_name] = fname

    to_download = []
    seen = set()

    for counter, (month, url) in enumerate(ordered_links, start=1):
        display_name = make_display_name(month, url)
        new_fname    = f"{counter:02d}_{display_name}"
        new_path     = os.path.join(dest_dir, new_fname)

        seen.add(display_name)

        if display_name in existing_map:
            old_fname = existing_map[display_name]
            old_path  = os.path.join(dest_dir, old_fname)
            if old_fname != new_fname:
                print(f"[RENAME] {old_fname}  →  {new_fname}")
                os.rename(old_path, new_path)
            else:
                print(f"[OK]     {new_fname}")
        else:
            print(f"[NEW]    {new_fname}")
            to_download.append((url, new_path))

    # Remove files no longer listed on site
    for display_name, fname in existing_map.items():
        if display_name not in seen:
            stale = os.path.join(dest_dir, fname)
            if os.path.exists(stale):
                os.remove(stale)
                print(f"[REMOVED] {fname}")

    return to_download

# ==== Main ====
async def main():
    html  = await fetch_rendered_html()
    links = extract_links(html)

    if not links:
        print("[!] No links found. The page may not have loaded correctly.")
        return

    print(f"Found {len(links)} PDF(s) on site:\n")
    for i, (month, url) in enumerate(links, 1):
        print(f"  {i:02d}. [{month}] {url.split('/')[-1]}")

    print(f"\nProcessing: {TARGET_DIR}\n" + "-" * 60)

    to_download = reorder_and_plan(TARGET_DIR, links)

    print("-" * 60)
    print(f"\nFiles to download: {len(to_download)}")

    if not to_download:
        print("Nothing new. All files up to date.")
        return

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        tasks = [async_download(session, url, dest) for url, dest in to_download]
        await asyncio.gather(*tasks)

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())