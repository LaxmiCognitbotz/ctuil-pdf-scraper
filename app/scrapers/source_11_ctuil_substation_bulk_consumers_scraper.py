"""
Scraper for: https://www.ctuil.in/substation-bulk-consumers
Download pdfs from the page.

Output Directory: uploads/CTUIL-Bulk-Consumers
"""

import os
import re
import ssl
import asyncio
from urllib.parse import unquote

import aiohttp
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError

load_dotenv(verbose=True)

BASE_URL = "https://ctuil.in/substation-bulk-consumers"
BASE_DIR = "uploads/CTUIL-Bulk-Consumers"

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


# ===== Safe Filename =====
def safe_filename(url: str) -> str:
    name = unquote(url.split("/")[-1].split("?")[0])
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)

    # split extension
    if "." in name:
        stem, ext = name.rsplit(".", 1)
        ext = "." + ext.lower()
    else:
        stem, ext = name, ".pdf"

    # remove timestamp
    stem = re.sub(r"^\d{6,}", "", stem).lstrip("_- ").strip()

    # normalize
    stem = stem.replace("_", " ")
    stem = re.sub(r"\s+", " ", stem).strip()

    # ===== Extract Date =====
    date = None

    # dd-mm-yyyy
    m = re.search(r"(\d{2}-\d{2}-\d{4})", stem)
    if m:
        date = m.group(1)

    # yyyy mm → convert to last day
    if not date:
        m = re.search(r"(20\d{2})[\s_]?(\d{2})", stem)
        if m:
            year = int(m.group(1))
            month = int(m.group(2))

            if month in [1,3,5,7,8,10,12]:
                day = 31
            elif month in [4,6,9,11]:
                day = 30
            else:
                day = 28

            date = f"{day:02d}-{month:02d}-{year}"

    # ddmmyyyy
    if not date:
        m = re.search(r"(\d{2})(\d{2})(20\d{2})", stem)
        if m:
            date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # final name
    if date:
        return f"Bulk Consumer {date}{ext}"

    return f"Bulk Consumer{ext}"


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

                await page.wait_for_selector("a", timeout=30_000)

                links = await page.evaluate("""() => {
                    const results = [];
                    const anchors = document.querySelectorAll("a");

                    anchors.forEach(a => {
                        if (!a.href) return;

                        const href = a.href.toLowerCase();
                        const text = a.innerText.toLowerCase();

                        if (href.includes(".pdf") && text.includes("bulk consumer")) {
                            results.push(a.href);
                        }
                    });

                    return results;
                }""")

                await browser.close()

            print("Page rendered.\n")
            return links

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


def reorder_and_plan(dest_dir, urls):
    os.makedirs(dest_dir, exist_ok=True)

    existing = {}
    for f in os.listdir(dest_dir):
        if "_" in f and f.split("_", 1)[0].isdigit():
            original = f.split("_", 1)[1]
            existing[original] = f

    # Handle duplicates in new URLs to match existing
    ordered_names = [safe_filename(u) for u in urls]
    seen_counts = {}
    for i, name in enumerate(ordered_names):
        seen_counts[name] = seen_counts.get(name, 0) + 1
        if seen_counts[name] > 1 and "." in name:
            base, ext = name.rsplit(".", 1)
            ordered_names[i] = f"{base}-{seen_counts[name]}.{ext}"
        elif seen_counts[name] > 1:
            ordered_names[i] = f"{name}-{seen_counts[name]}"

    tasks = []
    counter = 1

    for url, name in zip(urls, ordered_names):
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
    urls = await extract_links()

    print(f"Found {len(urls)} PDFs")

    connector = make_connector()

    async with aiohttp.ClientSession(connector=connector) as session:
        planned = reorder_and_plan(BASE_DIR, urls)

        print(f"Files to download: {len(planned)}")

        tasks = [async_download(session, url, dest) for url, dest in planned]
        await asyncio.gather(*tasks)

    print("\nDone")


if __name__ == "__main__":
    asyncio.run(main())