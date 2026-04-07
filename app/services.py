import os
from urllib.parse import unquote, urljoin
from playwright.sync_api import sync_playwright
from app.schemas import APIResponse

class DownloaderService:
    @staticmethod
    def run_margin_downloader():
        """Download Renewable Energy connectivity margin PDFs from CTUIL."""
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            url = "https://ctuil.in/renewable-energy"
            page.goto(url, wait_until="networkidle")

            # Wait for tables to be visible
            page.wait_for_selector("table")

            # Extract links from both target tables
            links_data = page.evaluate("""() => {
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

            download_dir = "uploads/margin_pdfs"
            os.makedirs(download_dir, exist_ok=True)

            downloaded_count = 0
            for i, pdf_url in enumerate(links_data):
                original_filename = unquote(pdf_url.split('/')[-1])
                
                file_name = f"{i+1:02d}_{original_filename}"
                file_path = os.path.join(download_dir, file_name)

                try:
                    response = page.request.get(pdf_url)
                    if response.status == 200:
                        with open(file_path, "wb") as f:
                            f.write(response.body())
                        downloaded_count += 1
                except Exception as e:
                    print(f"Error downloading {pdf_url}: {e}")

            browser.close()
            return {"downloaded_files": downloaded_count, "total_links_found": len(links_data)}

    @staticmethod
    def run_minutes_downloader():
        """Download ISTS Northern Region consultation meeting minutes."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto("https://ctuil.in/ists-consultation-meeting", wait_until="networkidle")

            # Preloader
            try:
                page.wait_for_selector(".preLoader", state="hidden", timeout=5000)
            except:
                pass

            # Filter for Northern Region
            page.click("a[title='Northern Region']", force=True)
            page.wait_for_timeout(3000)

            all_minutes_links = []
            while True:
                # Extract 'Minutes' links from the current page
                page_links = page.evaluate("""() => {
                    const rows = Array.from(document.querySelectorAll('table tbody tr'));
                    const headers = Array.from(document.querySelectorAll('table thead th, table tr th')).map(th => th.innerText.trim());
                    const minutesIdx = headers.findIndex(h => h.includes('Minutes'));
                    const regionIdx = headers.findIndex(h => h.includes('Region'));
                    
                    if (minutesIdx === -1) return [];

                    return rows.map(row => {
                        const cells = Array.from(row.cells);
                        const region = cells[regionIdx]?.innerText.trim();
                        if (region && !region.includes('Northern')) return null;

                        const minutesCell = cells[minutesIdx];
                        const link = minutesCell ? minutesCell.querySelector('a[href$=".pdf"]') : null;
                        return link ? link.href : null;
                    }).filter(href => href !== null);
                }""")

                all_minutes_links.extend(page_links)

                # Pagination
                next_button = page.query_selector('button[title="Goto Next Page"]')
                if next_button:
                    is_disabled = next_button.evaluate("btn => btn.disabled")
                    onclick_attr = next_button.get_attribute("onclick")
                    
                    if not is_disabled and onclick_attr:
                        next_button.click()
                        page.wait_for_timeout(3000)
                    else:
                        break
                else:
                    break

            # Download
            download_path = "uploads/minutes_pdfs"
            os.makedirs(download_path, exist_ok=True)

            downloaded_count = 0
            for i, url in enumerate(all_minutes_links):
                clean_name = unquote(url.split('/')[-1])
                file_path = os.path.join(download_path, f"{i+1}_{clean_name}")
                
                try:
                    response = page.request.get(url)
                    if response.status == 200:
                        with open(file_path, "wb") as f:
                            f.write(response.body())
                        downloaded_count += 1
                except Exception as e:
                    print(f"Error downloading {url}: {e}")

            browser.close()
            return {"downloaded_files": downloaded_count, "total_links_found": len(all_minutes_links)}

    @staticmethod
    def run_rtm_tbcb_downloader():
        """Download Northern Region RTM and TBCB PDFs."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            base_url = "https://ctuil.in"
            url = urljoin(base_url, "/rtmtbcb")
            page.goto(url, wait_until="networkidle")

            # Switch to NR tab
            page.click("a[data-bs-target='#reg_tab2']", force=True)
            page.wait_for_timeout(2000)

            # Extract links
            links_data = page.evaluate("""() => {
                const results = { rtm: [], tbcb: [] };
                const panel = document.querySelector('#reg_tab2');
                if (!panel) return results;

                const rows = Array.from(panel.querySelectorAll('table tr')).slice(1);
                
                rows.forEach(row => {
                    const cells = Array.from(row.cells);
                    if (cells.length >= 3) {
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

            rtm_dir = "uploads/rtm_pdfs"
            tbcb_dir = "uploads/tbcb_pdfs"
            os.makedirs(rtm_dir, exist_ok=True)
            os.makedirs(tbcb_dir, exist_ok=True)

            results = {"rtm_downloaded": 0, "tbcb_downloaded": 0}

            def download_files(links, folder, key):
                count = 0
                for i, pdf_url in enumerate(links):
                    original_filename = unquote(pdf_url.split('/')[-1])
                    file_name = f"{i+1:02d}_{original_filename}"
                    file_path = os.path.join(folder, file_name)

                    try:
                        response = page.request.get(pdf_url)
                        if response.status == 200:
                            with open(file_path, "wb") as f:
                                f.write(response.body())
                            count += 1
                    except Exception:
                        pass
                results[key] = count

            download_files(links_data['rtm'], rtm_dir, "rtm_downloaded")
            download_files(links_data['tbcb'], tbcb_dir, "tbcb_downloaded")

            browser.close()
            return {
                "rtm": {"downloaded": results["rtm_downloaded"], "found": len(links_data["rtm"])},
                "tbcb": {"downloaded": results["tbcb_downloaded"], "found": len(links_data["tbcb"])}
            }

    @staticmethod
    def run_cea_transmission_downloader():
        """Download Transmission reports from CEA website based on test.py logic."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            url = "https://cea.nic.in/transmission-reports/?lang=en"
            page.goto(url, wait_until="networkidle")
            page.wait_for_selector("tr", timeout=15000)

            target_reports = [
                "Regulated Tariff Mechanism (Under Construction Projects)",
                "Tariff Based Competitive Bidding Route (Completed Projects)",
                "Tariff Based Competitive Bidding Route (Under Construction Projects)"
            ]

            download_dir = "uploads/cea_transmission"
            os.makedirs(download_dir, exist_ok=True)

            rows = page.query_selector_all("tr")
            download_count = 0

            for row in rows:
                row_text = row.inner_text()
                for report_name in target_reports:
                    if report_name in row_text:
                        pdf_link = row.query_selector('a[title="Download Report"]')
                        if pdf_link:
                            with page.expect_download() as download_info:
                                pdf_link.click()
                            download = download_info.value
                            original_filename = download.suggested_filename
                            file_path = os.path.join(download_dir, original_filename)
                            download.save_as(file_path)
                            download_count += 1
                            break

            browser.close()
            return {"downloaded_files": download_count, "target_reports_count": len(target_reports)}