"""
Scraper for: https://www.ctuil.in/renewable-energy
Download pdfs from "Bays Allocation", "Connectivity margin in ists substations", "Proposed re integration" tables.

Output Directory: uploads/CTUIL-Renewable-Energy
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

BASE_URL = "https://www.ctuil.in/renewable-energy"
BASE_DIR = "uploads/CTUIL-Renewable-Energy"

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


def safe_filename(url: str) -> str:
    name = unquote(url.split("/")[-1].split("?")[0])

    # remove illegal chars
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)

    # split ext
    if "." in name:
        stem, ext = name.rsplit(".", 1)
        ext = "." + ext.lower()
    else:
        stem, ext = name, ".pdf"

    stem = re.sub(r"^\d{6,}", "", stem).lstrip("_- ").strip()

    # normalize
    stem = stem.replace("_", " ")
    stem = re.sub(r"\s+", " ", stem).strip()

    lower = stem.lower()

    if "allocation of bays" in lower:
        stem = re.sub(r"(?i)\b(approved|final|r\d+)\b", "", stem)
        stem = re.sub(r"\s+", " ", stem).strip()
        return f"{stem}{ext}"

    if "non re ss margin" in lower:
        stem = re.sub(r"(?i)\b(approved|final|rev[-\d]*)\b", "", stem)
        stem = re.sub(r"[-_]", " ", stem)
        stem = re.sub(r"\s+", " ", stem).strip()
        return f"{stem}{ext}"

    if "re ss margin" in lower:
        stem = re.sub(r"(?i)^re\s+", "", stem)  # remove leading RE
        stem = re.sub(r"(?i)\b(approved|final|rev[-\d]*)\b", "", stem)
        stem = re.sub(r"[-_]", " ", stem)
        stem = re.sub(r"\s+", " ", stem).strip()
        return f"{stem}{ext}"

    if "status of margins" in lower:
        stem = re.sub(r"\s+", " ", stem).strip()
        return f"{stem}{ext}"

    # fallback (safe)
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
                    const result = {
                        bays: [],
                        non_re: [],
                        re_substations: [],
                        proposed_re: []
                    };

                    const tables = Array.from(document.querySelectorAll('table'));

                    tables.forEach(table => {
                        const text = table.innerText.toLowerCase();

                        // ========= TABLE 1 =========
                        if (text.includes("connectivity margin in ists substations")) {
                            const rows = table.querySelectorAll("tr");

                            rows.forEach(row => {
                                const cells = row.querySelectorAll("td");

                                if (cells.length >= 4) {

                                    // NON-RE (column 3)
                                    const nonRe = cells[2].querySelector("a");
                                    if (nonRe && nonRe.href.toLowerCase().includes("pdf")) {
                                        result.non_re.push(nonRe.href);
                                    }

                                    // RE substations (column 4)
                                    const reSub = cells[3].querySelector("a");
                                    if (reSub && reSub.href.toLowerCase().includes("pdf")) {
                                        result.re_substations.push(reSub.href);
                                    }
                                }
                            });
                        }

                        // ========= TABLE 2 =========
                        else if (text.includes("proposed re integration")) {
                            const rows = table.querySelectorAll("tr");

                            rows.forEach(row => {
                                const link = row.querySelector("a");

                                if (link && link.href.toLowerCase().includes("pdf")) {
                                    result.proposed_re.push(link.href);
                                }
                            });
                        }

                        // ========= BAYS =========
                        else if (text.includes("allocation of bays")) {
                            const links = table.querySelectorAll("a[href]");
                            links.forEach(a => {
                                if (a.href.toLowerCase().includes("pdf")) {
                                    result.bays.push(a.href);
                                }
                            });
                        }
                    });

                    return result;
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
    return {"bays": [], "non_re": [], "re_substations": [], "proposed_re": []}

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

# ===== Shift + Incremental =====
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

# ===== Main =====
async def main():
    links_data = await extract_links()

    folder_map = {
        "bays": os.path.join(BASE_DIR, "Bays Allocation"),
        "non_re": os.path.join(BASE_DIR, "Margin", "Non-RE"),
        "re_substations": os.path.join(BASE_DIR, "Margin", "RE Substations"),
        "proposed_re": os.path.join(BASE_DIR, "Margin", "Proposed RE"),
    }

    connector = make_connector()

    async with aiohttp.ClientSession(connector=connector) as session:
        all_tasks = []

        for section, urls in links_data.items():
            if not urls:
                continue

            print(f"\nProcessing {section} ({len(urls)} files)")

            dest_dir = folder_map[section]
            planned = reorder_and_plan(dest_dir, urls)

            print(f"New files: {len(planned)}")

            for url, dest in planned:
                all_tasks.append(async_download(session, url, dest))

        await asyncio.gather(*all_tasks)

    print("\nDone")


if __name__ == "__main__":
    asyncio.run(main())