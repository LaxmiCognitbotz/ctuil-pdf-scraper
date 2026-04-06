# CTUIL PDF Downloader API

A robust, synchronous web scraping API built with FastAPI and Playwright to automate the collection of critical energy connectivity reports from the CTUIL website.

## Overview

This project provides a centralized API for downloading and archiving various PDF reports from the [CTUIL portal](https://ctuil.in/). It is designed for stability and simplicity, using a **synchronous architecture** to ensure reliable operation on Windows environments without the complexities of asynchronous event loops.

### Scraped Data
1.  **Connectivity Margins**: RE Substations available by 2030 and existing substation status.
2.  **NR Meeting Minutes**: ISTS Northern Region consultation meeting records.
3.  **RTM and TBCB**: Northern Region Real-Time Market and Tariff Based Competitive Bidding documents.

## Key Features

-   **Synchronous Stability**: Built using standard Python `def` routes and the Playwright Synchronous API for maximum reliability on Windows.
-   **Centralized Storage**: All downloaded PDFs are systematically organized in a root-level `uploads/` directory.
-   **Structured API Responses**: Every endpoint returns a consistent `APIResponse` schema with success status, descriptive messages, and a structured `APIError` object for failures.
-   **Headless Scraping**: Operates entirely in the background using Chromium.

## Prerequisites

-   Python 3.12 or higher
-   [uv](https://docs.astral.sh/uv/) (highly recommended for dependency management)

## Setup and Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/LaxmiCognitbotz/ctuil-pdf-scraper.git
    cd ctuil-pdf-scraper
    ```

2.  **Install dependencies**:
    Using `uv`:
    ```bash
    uv sync
    ```

3.  **Install Playwright browser**:
    ```bash
    uv run playwright install chromium
    ```

## Usage

Start the FastAPI server from the project root:

```bash
uv run python main.py
```

The API will be available at `http://localhost:8000`. You can visit `http://localhost:8000/docs` to access the interactive Swagger UI.

### API Endpoints (v1)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/download/margin` | Triggers the Margin PDF downloader |
| `POST` | `/api/v1/download/minutes` | Triggers the meeting minutes downloader |
| `POST` | `/api/v1/download/rtm-tbcb` | Triggers the RTM/TBCB downloader |
| `GET` | `/` | Health check endpoint |

## File Storage Structure

All downloads are archived in the `uploads/` directory:
-   `uploads/margin_pdfs/`
-   `uploads/minutes_pdfs/`
-   `uploads/rtm_pdfs/`
-   `uploads/tbcb_pdfs/`

## Project Layout

```
web-automation/
├── main.py                # API Entry Point
├── app/
│   ├── api.py             # Route definitions
│   ├── services.py        # Scraping logic (DownloaderService)
│   ├── schemas.py         # APIResponse & APIError models
│   └── __init__.py
├── config/
│   ├── msg.py             # Message utility
│   └── response_msg.json  # Centralized API messages
├── uploads/               # Central PDF repository
└── pyproject.toml         # Project metadata & dependencies
```
