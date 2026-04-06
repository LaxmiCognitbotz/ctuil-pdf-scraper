# ctuil-pdf-scraper

Automated scraper to fetch and archive Renewable Energy (RE) and ISTS connectivity margin PDFs from the CTUIL website.

## Overview
This repository contains an asynchronous Python scraper built with [Playwright](https://playwright.dev/python/). It visits the [CTUIL Renewable Energy portal](https://ctuil.in/renewable-energy) and automatically downloads the latest PDF reports regarding:
1. Connectivity Margin in ISTS RE Substations
2. Status of margins available at existing ISTS substations for proposed RE integration

The downloaded PDFs are systematically saved in the `ctuil_margin_downloader/margin_pdfs` directory for archiving and further analysis.

## Features
- **Headless Execution:** Runs silently in the background without opening a browser GUI.
- **Asynchronous Processing:** Built using Python's `asyncio` for fast and efficient scraping.
- **Auto-organization:** Automatically formats filenames and saves them to a designated directory.

## Prerequisites
- Python 3.10 or higher
- Git

## Setup and Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/LaxmiCognitbotz/ctuil-pdf-scraper.git
   cd ctuil-pdf-scraper
   ```

2. **Check/Install `uv`:**
   If you don't have [uv](https://docs.astral.sh/uv/) installed, install it first:
   - **On Windows:**
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - **On macOS/Linux:**
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```

3. **Create a virtual environment:**
   Use `uv` to create an isolated Python virtual environment:
   ```bash
   uv venv
   ```

4. **Sync project dependencies:**
   Pull in all the required packages defined in `pyproject.toml`:
   ```bash
   uv sync
   ```

5. **Install Playwright Browsers:**
   Once dependencies are synced, install the browser binaries inside the environment:
   ```bash
   uv run playwright install chromium
   ```

## Usage

To run the scraper and download the latest data:

```bash
uv run python ctuil_margin_downloader/ctuil_margin_downloader.py
```
*Note: `uv run` will automatically use the active `uv` virtual environment.*

## Structure
```
ctuil-pdf-scraper/
│
├── ctuil_margin_downloader/
│   ├── ctuil_margin_downloader.py  # Main scraper script
│   └── margin_pdfs/                # Directory where downloaded PDFs are saved
│
└── README.md                       # Project documentation
```
