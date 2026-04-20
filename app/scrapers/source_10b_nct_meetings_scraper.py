import os
import re
import asyncio
import aiohttp
from urllib.parse import unquote
from playwright.async_api import async_playwright

BASE_URL = "https://cea.nic.in/comm-trans/national-committee-on-transmission/?lang=en"
BASE_DIR = "uploads/cea_nct_minutes"

DOWNLOAD_SEM = asyncio.Semaphore(10)


# ===== safe filename =====
def safe_filename(url: str) -> str:
    name = unquote(url.split("/")[-1].split("?")[0])
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name.strip("._") or "file.pdf"

# ===== Extract Links =====
async def extract_links():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(BASE_URL)
        await page.wait_for_selector("table")

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
        return data

# ===== Download =====
async def async_download(session, url, dest):
    async with DOWNLOAD_SEM:
        try:
            if os.path.exists(dest):
                return

            async with session.get(url) as resp:
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
                os.rename(old_path, new_path)
        else:
            tasks.append((url, new_path))

        counter += 1

    return tasks

# ===== Main =====
async def main():
    print("Extracting links...")
    items = await extract_links()

    print(f"Found {len(items)} Minutes PDFs")

    # SSL bypass
    connector = aiohttp.TCPConnector(ssl=False)

    async with aiohttp.ClientSession(connector=connector) as session:
        planned = reorder_and_plan(BASE_DIR, items)

        print(f"New files to download: {len(planned)}")

        tasks = [async_download(session, url, dest) for url, dest in planned]
        await asyncio.gather(*tasks)

    print("\nDone")


if __name__ == "__main__":
    asyncio.run(main())