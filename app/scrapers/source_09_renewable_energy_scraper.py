import os
import re
import asyncio
import aiohttp
from urllib.parse import unquote
from playwright.async_api import async_playwright

BASE_URL = "https://www.ctuil.in/renewable-energy"
BASE_DIR = "uploads/renewable_energy"

DOWNLOAD_SEM = asyncio.Semaphore(10)


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
                os.rename(old_path, new_path)
        else:
            tasks.append((url, new_path))

        counter += 1

    return tasks

# ===== Main =====
async def main():
    links_data = await extract_links()

    folder_map = {
        "bays": os.path.join(BASE_DIR, "bays_allocation"),
        "non_re": os.path.join(BASE_DIR, "margin", "non_re"),
        "re_substations": os.path.join(BASE_DIR, "margin", "re_substations"),
        "proposed_re": os.path.join(BASE_DIR, "margin", "proposed_re"),
    }

    async with aiohttp.ClientSession() as session:
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