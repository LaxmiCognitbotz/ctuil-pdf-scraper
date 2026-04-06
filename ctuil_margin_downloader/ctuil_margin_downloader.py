import os
import asyncio
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def download_re_margin_pdfs():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://ctuil.in/renewable-energy"
        await page.goto(url, wait_until="networkidle")

        # Wait for tables to be visible
        await page.wait_for_selector("table")

        # Extract links from both target tables
        links_data = await page.evaluate("""() => {
            const results = [];
            const tables = Array.from(document.querySelectorAll('table'));
            
            // TABLE 1: Connectivity Margin in ISTS RE Substations available by Mar-2030
            const table1 = tables.find(t => t.innerText.includes('Connectivity Margin in ISTS RE Substations available by Mar-2030'));
            if (table1) {
                Array.from(table1.querySelectorAll('tr')).forEach(row => {
                    const cells = Array.from(row.cells);
                    if (cells.length >= 4) {
                        const pdfLink = cells[3].querySelector('a'); 
                        if (pdfLink && pdfLink.href.toLowerCase().endsWith('.pdf')) {
                            results.push(pdfLink.href);
                        }
                    }
                });
            }

            // TABLE 2: Status of margins available at existing ISTS substations...
            const table2 = tables.find(t => t.innerText.includes('Status of margins available at existing ISTS substations for proposed RE integration as on'));
            if (table2) {
                Array.from(table2.querySelectorAll('tr')).forEach(row => {
                    const cells = Array.from(row.cells);
                    if (cells.length >= 3) {
                        const pdfLink = cells[2].querySelector('a'); 
                        if (pdfLink && pdfLink.href.toLowerCase().endsWith('.pdf')) {
                            results.push(pdfLink.href);
                        }
                    }
                });
            }
            
            return results;
        }""")

        download_dir = "ctuil_margin_downloader/margin_pdfs"
        os.makedirs(download_dir, exist_ok=True)

        for i, pdf_url in enumerate(links_data):
            original_filename = unquote(pdf_url.split('/')[-1])
            
            file_name = f"{i+1:02d}_{original_filename}"
            file_path = os.path.join(download_dir, file_name)

            try:
                response = await page.request.get(pdf_url)
                if response.status == 200:
                    with open(file_path, "wb") as f:
                        f.write(await response.body())
                else:
                    print(f"Failed to download {pdf_url}: Status {response.status}")
            except Exception as e:
                print(f"Error downloading {pdf_url}: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_re_margin_pdfs())