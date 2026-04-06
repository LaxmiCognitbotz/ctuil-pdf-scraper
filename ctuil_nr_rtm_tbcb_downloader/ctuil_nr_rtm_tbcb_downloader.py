import os
import asyncio
from playwright.async_api import async_playwright
from urllib.parse import unquote, urljoin

async def download_rtm_tbcb_nr():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        base_url = "https://ctuil.in"
        url = urljoin(base_url, "/rtmtbcb")
        
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")

        # Click the NR tab
        # Based on inspection, NR tab triggers panel #reg_tab2
        print("Switching to Northern Region (NR) tab...")
        await page.click("a[data-bs-target='#reg_tab2']", force=True)
        await page.wait_for_timeout(2000) # Wait for tab content to be ready

        # Extract links from the NR table
        print("Extracting PDF links from RTM and TBCB columns...")
        links_data = await page.evaluate("""() => {
            const results = { rtm: [], tbcb: [] };
            const panel = document.querySelector('#reg_tab2');
            if (!panel) return results;

            const rows = Array.from(panel.querySelectorAll('table tr')).slice(1); // Skip header row
            
            rows.forEach(row => {
                const cells = Array.from(row.cells);
                if (cells.length >= 3) {
                    // Column 1: Month, Column 2: RTM link, Column 3: TBCB link
                    const rtmLink = cells[1].querySelector('a');
                    const tbcbLink = cells[2].querySelector('a');

                    if (rtmLink && rtmLink.href.toLowerCase().endsWith('.pdf')) {
                        results.rtm.push(rtmLink.href);
                    }
                    if (tbcbLink && tbcbLink.href.toLowerCase().endsWith('.pdf')) {
                        results.tbcb.push(tbcbLink.href);
                    }
                }
            });
            return results;
        }""")

        rtm_dir = "ctuil_nr_rtm_tbcb_downloader/RTM_pdfs"
        tbcb_dir = "ctuil_nr_rtm_tbcb_downloader/TBCB_pdfs"
        os.makedirs(rtm_dir, exist_ok=True)
        os.makedirs(tbcb_dir, exist_ok=True)

        # Function to download and save
        async def download_files(links, folder):
            total = len(links)
            for i, pdf_url in enumerate(links):
                original_filename = unquote(pdf_url.split('/')[-1])
                file_name = f"{i+1:02d}_{original_filename}"
                file_path = os.path.join(folder, file_name)

                print(f"Downloading [{i+1}/{total}] to {folder}: {original_filename}")
                try:
                    response = await page.request.get(pdf_url)
                    if response.status == 200:
                        with open(file_path, "wb") as f:
                            f.write(await response.body())
                except Exception:
                    pass

        # Execute downloads for both categories
        await download_files(links_data['rtm'], rtm_dir)
        await download_files(links_data['tbcb'], tbcb_dir)

        await browser.close()
        print("Done! All NR files downloaded.")

if __name__ == "__main__":
    asyncio.run(download_rtm_tbcb_nr())