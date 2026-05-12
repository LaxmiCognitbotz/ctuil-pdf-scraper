"""
Scraper for: https://cea.nic.in/comm-trans/national-committee-on-transmission/?lang=en
Download Minutes and MoM pdfs from the page.

Output Directory: uploads/CEA-NCT-Minutes
"""

import os
import re
import ssl
import asyncio
import aiohttp

from urllib.parse import unquote
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from dotenv import load_dotenv

load_dotenv(verbose=True)

BASE_URL = "https://cea.nic.in/comm-trans/national-committee-on-transmission/?lang=en"
BASE_DIR = "uploads/CEA-NCT-Minutes"

DOWNLOAD_SEM = asyncio.Semaphore(10)

# ==== Proxy Settings ====
PROXY_ENABLED      = os.getenv("PROXY_ENABLED", "false").lower() == "true"
PROXY_URL          = os.getenv("PROXY_URL", "")
PROXY_INSECURE_SSL = os.getenv("PROXY_INSECURE_SSL", "false").lower() == "true"

PLAYWRIGHT_RETRIES = 3

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
    "--disable-dev-tools",
    "--disable-hang-monitor",
    "--disable-prompt-on-repost",
    "--disable-client-side-phishing-detection",
    "--password-store=basic",
]


# ==== Proxy Helpers ====
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


# ===== safe filename =====
def safe_filename(url: str) -> str:
    name = unquote(url.split("/")[-1].split("?")[0])

    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)

    # split ext
    if "." in name:
        stem, ext = name.rsplit(".", 1)
        ext = "." + ext.lower()
    else:
        stem, ext = name, ".pdf"

    # ==== Clean stem ====
    stem = stem.replace("_", " ")
    stem = re.sub(r"\s+", " ", stem).strip()

    m = re.search(r"\b(\d{1,3})(st|nd|rd|th)\b", stem, re.I)

    if m:
        ordinal = f"{m.group(1)}{m.group(2).lower()}"
        return f"{ordinal}_NCT_MoM{ext}"

    m = re.search(r"\b(\d{1,3})\b", stem)
    if m:
        num = int(m.group(1))

        # convert to ordinal
        if 10 <= num % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(num % 10, "th")

        return f"{num}{suffix}_NCT_MoM{ext}"

    return f"{stem}{ext}" if stem else f"file{ext}"

# ===== Extract Links =====
async def extract_links():
    last_error = None

    for attempt in range(1, PLAYWRIGHT_RETRIES + 1):
        print(f"Launching headless browser...")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=CHROMIUM_ARGS,
                )
                context = await browser.new_context(
                    ignore_https_errors=True,
                    proxy={"server": PROXY_URL} if PROXY_ENABLED and PROXY_URL else None,
                )
                page = await context.new_page()

                await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60_000)

                try:
                    await page.wait_for_load_state("networkidle", timeout=15_000)
                except PWTimeoutError:
                    pass

                await page.wait_for_selector("table", timeout=30_000)

                data = await page.evaluate("""() => {
                    const results = [];
                    const rows = document.querySelectorAll("table tbody tr");

                    rows.forEach(row => {
                        const links = row.querySelectorAll("a");

                        links.forEach(link => {
                            if (!link.href) return;

                            const href = link.href.toLowerCase();
                            const text = link.innerText.toLowerCase();

                            // only PDF
                            if (!href.includes(".pdf")) return;

                            // capture both Minutes + MoM
                            if (text.includes("minutes") || text.includes("mom")) {
                                results.push({
                                    url: link.href,
                                    title: row.innerText.trim()
                                });
                            }
                        });
                    });

                    return results;
                }""")

                await browser.close()

            print("Page rendered.\n")
            return data

        except PWTimeoutError as e:
            last_error = e
            if attempt < PLAYWRIGHT_RETRIES:
                await asyncio.sleep(attempt * 5)

        except Exception as e:
            last_error = e
            if attempt < PLAYWRIGHT_RETRIES:
                await asyncio.sleep(5)

    print(f"[!] Failed to fetch page after {PLAYWRIGHT_RETRIES} attempts. Last error: {last_error}")
    return []

# ===== Download =====
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

            with open(dest, "wb") as f:
                f.write(data)

            print(f"Saved: {os.path.basename(dest)}")

        except Exception as e:
            print(f"Error: {url} → {e}")

# ===== Order + Plan =====
def reorder_and_plan(dest_dir, items):
    os.makedirs(dest_dir, exist_ok=True)

    existing = {}
    for f in os.listdir(dest_dir):
        if "_" in f:
            original = f.split("_", 1)[1]
            existing[original] = f

    tasks = []
    counter = 1

    for item in items:
        url = item["url"]
        name = safe_filename(url)

        new_name = f"{counter:02d}_{name}"
        new_path = os.path.join(dest_dir, new_name)

        if name in existing:
            old_path = os.path.join(dest_dir, existing[name])
            if old_path != new_path:
                os.replace(old_path, new_path)
        else:
            tasks.append((url, new_path))

        counter += 1

    return tasks

# ===== Main =====
async def main():
    print("Extracting links...")
    items = await extract_links()

    print(f"Found {len(items)} Minutes PDFs")

    connector = make_connector()

    async with aiohttp.ClientSession(connector=connector) as session:
        planned = reorder_and_plan(BASE_DIR, items)

        print(f"New files to download: {len(planned)}")

        tasks = [async_download(session, url, dest) for url, dest in planned]
        await asyncio.gather(*tasks)

    print("\nDone")


if __name__ == "__main__":
    asyncio.run(main())