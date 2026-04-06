import os
import asyncio
from playwright.async_api import async_playwright
from urllib.parse import unquote

async def capture_all_northern_minutes():
    async with async_playwright() as p:
        # headless=False helps you see if it's clicking through correctly
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to CTUIL website...")
        await page.goto("https://ctuil.in/ists-consultation-meeting", wait_until="networkidle")

        # Preloader
        try:
            await page.wait_for_selector(".preLoader", state="hidden", timeout=5000)
        except:
            pass

        # Filter for Northern Region
        await page.click("a[title='Northern Region']", force=True)
        await page.wait_for_timeout(3000)

        all_minutes_links = []
        page_number = 1

        while True:
            # Extract 'Minutes' links from the current page
            page_links = await page.evaluate("""() => {
                const rows = Array.from(document.querySelectorAll('table tbody tr'));
                const headers = Array.from(document.querySelectorAll('table thead th, table tr th')).map(th => th.innerText.trim());
                const minutesIdx = headers.findIndex(h => h.includes('Minutes'));
                const regionIdx = headers.findIndex(h => h.includes('Region'));
                
                if (minutesIdx === -1) return [];

                return rows.map(row => {
                    const cells = Array.from(row.cells);
                    // Double check region filter even after click to be safe
                    const region = cells[regionIdx]?.innerText.trim();
                    if (region && !region.includes('Northern')) return null;

                    const minutesCell = cells[minutesIdx];
                    const link = minutesCell ? minutesCell.querySelector('a[href$=".pdf"]') : null;
                    return link ? link.href : null;
                }).filter(href => href !== null);
            }""")

            all_minutes_links.extend(page_links)

            # Check for 'Next' button and Click it
            # The next button is inside the pagination div with title "Goto Next Page"
            next_button = await page.query_selector('button[title="Goto Next Page"]')
            
            # Check if next button is disabled or points to current page
            if next_button:
                is_disabled = await next_button.evaluate("btn => btn.disabled")
                onclick_attr = await next_button.get_attribute("onclick")
                
                if not is_disabled and onclick_attr:
                    await next_button.click()
                    await page.wait_for_timeout(3000)
                    page_number += 1
                else:
                    break
            else:
                break

        # Download
        download_path = "ctuil_nr_minutes_downloader/northern_region_minutes_pdfs"
        os.makedirs(download_path, exist_ok=True)

        for i, url in enumerate(all_minutes_links):
            clean_name = unquote(url.split('/')[-1])
            file_path = os.path.join(download_path, f"{i+1}_{clean_name}")
            
            print(f"Downloading [{i+1}/{len(all_minutes_links)}]: {clean_name}")
            try:
                response = await page.request.get(url)
                if response.status == 200:
                    with open(file_path, "wb") as f:
                        f.write(await response.body())
            except Exception as e:
                print(f"Error downloading {url}: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_all_northern_minutes())