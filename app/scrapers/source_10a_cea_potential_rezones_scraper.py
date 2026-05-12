"""
Scraper for: https://cea.nic.in/psp___a_i/transmission-system-for-integration-of-over-500-gw-non-fossil-capacity-by-2030/?lang=en
Download pdfs from the page.

Output Directory: uploads/CEA-500GW
"""

import os
import re
import ssl
import asyncio
from urllib.parse import unquote

import aiohttp
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from dotenv import load_dotenv

load_dotenv(verbose=True)

BASE_URL = "https://cea.nic.in/psp___a_i/transmission-system-for-integration-of-over-500-gw-non-fossil-capacity-by-2030/?lang=en"
BASE_DIR = "uploads/CEA-500GW"

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
    return name.strip("._") or "file.pdf"


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

                        // only PDFs
                        if (href.includes(".pdf")) {
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


# ================= DOWNLOAD =================
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


# ================= ORDER =================
def reorder_and_plan(dest_dir, urls):
    os.makedirs(dest_dir, exist_ok=True)

    existing = {}
    for f in os.listdir(dest_dir):
        if "_" in f:
            original = f.split("_", 1)[1]
            existing[original] = f

    tasks = []
    counter = 1

    for url in urls:
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


# ================= MAIN =================
async def main():
    print("Extracting links...")
    urls = await extract_links()

    print(f"Found {len(urls)} PDFs")

    connector = make_connector()

    async with aiohttp.ClientSession(connector=connector) as session:
        planned = reorder_and_plan(BASE_DIR, urls)

        print(f"New files to download: {len(planned)}")

        tasks = [async_download(session, url, dest) for url, dest in planned]
        await asyncio.gather(*tasks)

    print("\nDone")


if __name__ == "__main__":
    asyncio.run(main())