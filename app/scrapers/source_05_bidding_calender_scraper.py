import os
import re
import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

BASE_URL = "https://www.ctuil.in/bidding-calendar"
DOWNLOAD_DIR = "uploads/bidding_calendar"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

DOWNLOAD_SEM = asyncio.Semaphore(10)


# ==== Safe Filename ====
def safe_filename(url: str) -> str:
    name = unquote(url.split("/")[-1].split("?")[0])
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name.strip("._") or "file.pdf"

# ==== Fetch Links ====
def fetch_pdf_links():
    response = requests.get(BASE_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    pdf_links = []
    seen = set()

    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        href = a["href"]

        if "bidding calendar" in text and href.lower().endswith(".pdf"):
            full_url = urljoin(BASE_URL, href)

            if full_url not in seen:
                seen.add(full_url)
                pdf_links.append(full_url)

    return pdf_links

# ==== Download ====
async def async_download(session, url, dest):
    async with DOWNLOAD_SEM:
        try:
            if os.path.exists(dest):
                return

            async with session.get(url) as resp:
                if resp.status != 200:
                    return
                data = await resp.read()

            with open(dest, "wb") as f:
                f.write(data)

            print(f"[OK] {os.path.basename(dest)}")

        except Exception as e:
            print(f"[ERROR] {url} → {e}")

# ==== Shift + Incremental ====
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
                os.rename(old_path, new_path)
        else:
            tasks.append((url, new_path))

        counter += 1

    return tasks

# ==== Main ====
async def main():
    urls = fetch_pdf_links()

    print(f"Total PDFs found: {len(urls)}")

    # IMPORTANT: assume site already gives latest first
    planned = reorder_and_plan(DOWNLOAD_DIR, urls)

    print(f"New files to download: {len(planned)}")

    async with aiohttp.ClientSession() as session:
        tasks = [async_download(session, url, dest) for url, dest in planned]
        await asyncio.gather(*tasks)

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())