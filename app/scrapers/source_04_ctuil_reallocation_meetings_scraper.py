"""
Scraper for: https://www.ctuil.in/reallocation_meetings
Download PDFs from "Agenda" and "Minutes" columns for each region.

Output Directory: uploads/CTUIL-Reallocation-Meetings
"""

import os
import re
import ssl
import asyncio
from urllib.parse import unquote, urljoin, quote

import aiohttp
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from dotenv import load_dotenv

load_dotenv(verbose=True)

BASE_URL = "https://www.ctuil.in/reallocation_meetings"
BASE_DIR = "uploads/CTUIL-Reallocation-Meetings"

DOWNLOAD_SEM = asyncio.Semaphore(10)

PROXY_ENABLED      = os.getenv("PROXY_ENABLED", "false").lower() == "true"
PROXY_URL          = os.getenv("PROXY_URL", "")
PROXY_INSECURE_SSL = os.getenv("PROXY_INSECURE_SSL", "false").lower() == "true"

PLAYWRIGHT_RETRIES = 3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

CHROMIUM_ARGS = [
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-default-apps",
    "--disable-sync",
    "--disable-translate",
    "--no-first-run",
    "--no-default-browser-check",
    "--mute-audio",
    "--ignore-certificate-errors",
    "--ignore-ssl-errors",
    "--disable-hang-monitor",
    "--disable-prompt-on-repost",
    "--password-store=basic",
]


def get_proxy() -> str | None:
    return PROXY_URL if PROXY_ENABLED else None

def get_ssl_context():
    if PROXY_INSECURE_SSL:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return None

def make_connector() -> aiohttp.TCPConnector:
    return aiohttp.TCPConnector(ssl=get_ssl_context())


def safe_filename(url: str) -> str:
    name = unquote(url.split("/")[-1].split("?")[0])
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name.strip("._") or "file.pdf"


def strip_leading_timestamp(filename: str) -> str:
    # Remove long numeric prefixes used as timestamps/ids (keep meaningful small ordinals like "2nd ...").
    if "." in filename:
        stem, ext = filename.rsplit(".", 1)
        ext = "." + ext
    else:
        stem, ext = filename, ""

    stem = re.sub(r"^\d{9,}\s*(?:pdf)?[_\-\s]*", "", stem, flags=re.IGNORECASE).strip()
    stem = re.sub(r"\s+", " ", stem).strip()
    return f"{stem}{ext}" if stem else filename


def display_name_from_url(url: str) -> str:
    return strip_leading_timestamp(safe_filename(url))


def ensure_doc_type_dir(region: str, doc_type: str) -> str:
    new_dir = os.path.join(BASE_DIR, region, doc_type)
    legacy_dir = os.path.join(BASE_DIR, region, doc_type.lower())

    if os.path.isdir(legacy_dir) and legacy_dir != new_dir:
        os.makedirs(new_dir, exist_ok=True)
        for name in os.listdir(legacy_dir):
            src = os.path.join(legacy_dir, name)
            dst = os.path.join(new_dir, name)
            if not os.path.exists(dst):
                os.replace(src, dst)
        try:
            os.rmdir(legacy_dir)
        except OSError:
            pass

    return new_dir

# ==== Incremental Logic ====
def apply_incremental_update(dest_dir, urls):
    os.makedirs(dest_dir, exist_ok=True)

    # normalize incoming (strip timestamp right after the NN_ prefix)
    ordered = [display_name_from_url(u) for u in urls]

    # If the same display name appears multiple times, keep them unique but stable.
    seen_counts = {}
    for i, name in enumerate(ordered):
        seen_counts[name] = seen_counts.get(name, 0) + 1
        if seen_counts[name] > 1 and "." in name:
            base, ext = name.rsplit(".", 1)
            ordered[i] = f"{base}-{seen_counts[name]}.{ext}"
        elif seen_counts[name] > 1:
            ordered[i] = f"{name}-{seen_counts[name]}"

    # existing files
    existing = {}
    for f in os.listdir(dest_dir):
        lookup = f.split("_", 1)[1] if "_" in f and f.split("_", 1)[0].isdigit() else f
        existing.setdefault(lookup, f)
        existing.setdefault(strip_leading_timestamp(lookup), f)

    download_list = []

    for idx, original_name in enumerate(ordered, start=1):
        new_name = f"{idx:02d}_{original_name}"
        new_path = os.path.join(dest_dir, new_name)

        if original_name in existing:
            old_path = os.path.join(dest_dir, existing[original_name])
            if old_path != new_path:
                os.replace(old_path, new_path)
        else:
            # Find the matching URL for this display name (including any "-2" suffix).
            download_list.append((urls[idx - 1], new_path))

    return download_list

# ==== Extract Pipeline ====
async def extract_all_regions(page):
    all_links = []

    tabs = await page.query_selector_all("ul.nav li a")

    for i, tab in enumerate(tabs):
        region = (await tab.inner_text()).strip()
        print(f"\nProcessing Region: {region}")

        if i != 0:
            await tab.click()
            await asyncio.sleep(1)

        active_tab = await page.query_selector(".tab-pane.active")

        if not active_tab:
            print(f"{region} → No active tab found (skipping)")
            continue

        rows = await active_tab.query_selector_all("tbody tr")

        if not rows:
            print(f"{region} → No rows (skipping)")
            continue

        region_links = []

        for row in rows:
            cols = await row.query_selector_all("td")

            if len(cols) < 3:
                continue

            # ===== Agenda =====
            agenda_a = await cols[1].query_selector("a")
            if agenda_a:
                href = await agenda_a.get_attribute("href")
                if href and ".pdf" in href.lower():
                    href = urljoin(BASE_URL, href)
                    href = quote(href, safe=":/")
                    region_links.append((region, "Agenda", href))

            # ===== Minutes =====
            minutes_a = await cols[2].query_selector("a")
            if minutes_a:
                href = await minutes_a.get_attribute("href")
                if href and ".pdf" in href.lower():
                    href = urljoin(BASE_URL, href)
                    href = quote(href, safe=":/")
                    region_links.append((region, "Minutes", href))

        if not region_links:
            print(f"{region} → No PDFs (skipping)")
            continue

        print(f"{region} → Found {len(region_links)} PDFs")
        all_links.extend(region_links)

    return all_links

# ==== Download Pipeline ====
async def async_download(session, url, dest):
    proxy = get_proxy()
    async with DOWNLOAD_SEM:
        try:
            if os.path.exists(dest):
                return

            async with session.get(url, proxy=proxy, timeout=aiohttp.ClientTimeout(total=90)) as resp:
                if resp.status != 200:
                    print(f"Failed {resp.status}: {url}")
                    return

                data = await resp.read()

            os.makedirs(os.path.dirname(dest), exist_ok=True)

            with open(dest, "wb") as f:
                f.write(data)

            print(f"Saved: {dest}")

        except Exception as e:
            print(f"Error: {url} → {e}")

# ==== Main Pipeline ====
async def main():
    last_error = None
    links = None

    for attempt in range(1, PLAYWRIGHT_RETRIES + 1):
        print(f"Launching headless browser (attempt {attempt}/{PLAYWRIGHT_RETRIES})...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=CHROMIUM_ARGS,
                )
                context = await browser.new_context(
                    ignore_https_errors=True,
                    user_agent=HEADERS["User-Agent"],
                    extra_http_headers={"Accept-Language": HEADERS["Accept-Language"]},
                    proxy={"server": PROXY_URL} if PROXY_ENABLED and PROXY_URL else None,
                )
                page = await context.new_page()

                await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60_000)

                try:
                    await page.wait_for_load_state("networkidle", timeout=15_000)
                except PWTimeoutError:
                    print("  [WARN] networkidle timeout — continuing anyway.")

                await page.wait_for_selector("table", timeout=30_000)

                links = await extract_all_regions(page)
                await browser.close()

            print("Page rendered successfully.\n")
            break

        except PWTimeoutError as e:
            last_error = e
            print(f"  [TIMEOUT] Attempt {attempt} failed: {e}")
            if attempt < PLAYWRIGHT_RETRIES:
                wait_secs = attempt * 5
                print(f"  Retrying in {wait_secs}s …")
                await asyncio.sleep(wait_secs)

        except Exception as e:
            last_error = e
            print(f"  [ERROR] Attempt {attempt}: {e}")
            if attempt < PLAYWRIGHT_RETRIES:
                await asyncio.sleep(5)

    if not links:
        print(f"[!] Failed to fetch page after {PLAYWRIGHT_RETRIES} attempts. Last error: {last_error}")
        return

    seen = set()
    unique_links = []
    for item in links:
        if item not in seen:
            seen.add(item)
            unique_links.append(item)
    links = unique_links

    print(f"\nTotal unique PDFs: {len(links)}")

    # Group by region + type
    grouped = {}
    for region, doc_type, url in links:
        grouped.setdefault((region, doc_type), []).append(url)

    connector = make_connector()

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for (region, doc_type), urls in grouped.items():
            dest_dir = ensure_doc_type_dir(region, doc_type)

            # Apply incremental logic
            to_download = apply_incremental_update(dest_dir, urls)
            for url, dest in to_download:
                tasks.append(async_download(session, url, dest))

        await asyncio.gather(*tasks)

    print("\nDone")


if __name__ == "__main__":
    asyncio.run(main())