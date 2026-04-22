# CTUIL / CEA Scraper API

A REST API built with **FastAPI** that automates PDF extraction and download from the [CTUIL](https://ctuil.in/) and [CEA](https://cea.nic.in/) websites. Each scraper runs as a self-contained module — the API wraps them without modifying any original script logic.

## Overview

This project consolidates **12 independent scrapers** into a single API platform. Scrapers target two primary data sources:

- **CTUIL** (ctuil.in) — Consultation meetings, coordination meetings, RE generators, reallocation meetings, bidding calendars, compliance reports, revocations, renewable energy margins, and bulk consumer data.
- **CEA** (cea.nic.in) — Transmission reports (RTM/TBCB), 500 GW RE integration documents, and NCT meeting minutes.

All downloaded PDFs are organized into the `uploads/` directory with incremental naming and deduplication.

## Key Features

- **12 scraper endpoints** covering CTUIL and CEA data sources
- **Strict wrapper architecture** — scraper scripts are imported and called as black boxes, never modified
- **Consistent API responses** — every endpoint returns a standardized `APIResponse` envelope with status, message, data, error, and UTC timestamp
- **Proper HTTP status codes** — 200 on success, 500 on failure with full traceback
- **Incremental downloads** — scripts detect existing files and only download new ones
- **Swagger UI** — interactive API docs at `/docs` with organized tag groups

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management

## Setup

```bash
# Clone
git clone https://github.com/LaxmiCognitbotz/ctuil-pdf-scraper.git
cd ctuil-pdf-scraper

# Install dependencies
uv sync

# Install Playwright browser
uv run playwright install chromium
```

## Usage

```bash
uv run python main.py
```

The API starts at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the Swagger UI.

## API Endpoints (v1)

### Health & Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/v1/scrapers` | List all available scrapers with metadata |

### CTUIL Scrapers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/scrape/ists-consultation-meeting` | Agenda & Minutes for all 5 regions |
| `POST` | `/api/v1/scrape/ists-joint-coordination-meeting` | Notice & Minutes for all regions |
| `POST` | `/api/v1/scrape/regenerators` | Effective-date-wise connectivity PDFs |
| `POST` | `/api/v1/scrape/reallocation-meetings` | Agenda & Minutes for all regions |
| `POST` | `/api/v1/scrape/bidding-calendar` | Bidding Calendar PDFs |
| `POST` | `/api/v1/scrape/compliance-fc` | Connectivity Grantee PDFs |
| `POST` | `/api/v1/scrape/monitoring-connectivity` | Revocation & Monitoring PDFs |
| `POST` | `/api/v1/scrape/renewable-energy` | RE margin & Bays Allocation PDFs |
| `POST` | `/api/v1/scrape/substation-bulk-consumers` | Bulk Consumer PDFs |

### CEA Scrapers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/scrape/transmission-reports` | RTM & TBCB reports (last 24 months) |
| `POST` | `/api/v1/scrape/potential-re-zones` | 500 GW RE Integration PDFs |
| `POST` | `/api/v1/scrape/nct-meetings` | NCT meeting minutes |

## Project Structure

```
ctuil-pdf-scraper/
├── main.py                    # App entry point, router registration
├── pyproject.toml             # Dependencies & project metadata
│
├── app/
│   ├── __init__.py
│   ├── catalog.py             # Scraper metadata for discovery endpoint
│   ├── helpers.py             # Shared request handler, execute_scraper & error responses
│   ├── schemas.py             # APIResponse & APIError models
│   │
│   ├── modules/
│   │   ├── health/
│   │   │   └── routes.py      # GET /  +  GET /api/v1/scrapers
│   │   │
│   │   ├── ctuil/
│   │   │   ├── routes.py      # 9 CTUIL POST endpoints
│   │   │   └── services.py    # 9 CTUIL service methods
│   │   │
│   │   └── cea/
│   │       ├── routes.py      # 3 CEA POST endpoints
│   │       └── services.py    # 3 CEA service methods
│   │
│   └── scrapers/              # Original scripts (untouched)
│       ├── __init__.py
│       ├── source_01_ctuil_ists_consultation_meeting_scraper.py
│       ├── source_02_ctuil_ists_joint_coordination_meeting_scraper.py
│       ├── source_03_ctuil_regenerators_scraper.py
│       ├── source_04_ctuil_reallocation_meetings_scraper.py
│       ├── source_05_ctuil_bidding_calender_scraper.py
│       ├── source_06_ctuil_transmission_reports_scraper.py
│       ├── source_07_ctuil_compliance_fc_scraper.py
│       ├── source_08_ctuil_monitoring_connectivity_scraper.py
│       ├── source_09_ctuil_renewable_energy_scraper.py
│       ├── source_10a_cea_potential_rezones_scraper.py
│       ├── source_10b_cea_nct_meetings_scraper.py
│       └── source_11_ctuil_substation_bulk_consumers_scraper.py
│
└── uploads/                   # All downloaded PDFs (auto-created)
    ├── CTUIL-ISTS-CMETS/
    ├── CTUIL-ISTS-JCC/
    ├── CTUIL-Regenerators-Effective-Date-wise/
    ├── CTUIL-Reallocation-Meetings/
    ├── CTUIL-Bidding-Calendar/
    ├── CTUIL-Compliance-PDFs/
    ├── CTUIL-Revocations-PDFs/
    ├── CTUIL-Renewable-Energy/
    ├── CTUIL-Bulk-Consumers/
    ├── CTUIL-Transmission-Reports/
    ├── CEA-500GW/
    └── CEA-NCT-Minutes/
```

## Tech Stack

- **FastAPI** — REST framework
- **Playwright** — Browser automation for JS-rendered pages
- **aiohttp** — Async HTTP downloads
- **BeautifulSoup4** — HTML parsing
- **requests** — Sync HTTP calls (CEA scraper)
- **uv** — Dependency management
