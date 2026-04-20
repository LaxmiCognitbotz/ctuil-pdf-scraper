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

## Response Format

Every endpoint returns:

```json
{
  "status": true,
  "message": "RE Generators scraper completed successfully.",
  "data": {
    "script": "source_03_regenerators_scraper",
    "execution_time_seconds": 18.42,
    "output_dir": "uploads/Effective_Date_Wise"
  },
  "error": null,
  "timestamp": "2026-04-20T10:29:50.093180+00:00"
}
```

On failure, `status` is `false` and `error` contains `code` and `detail` (full traceback).

## Project Structure

```
ctuil-pdf-scraper/
├── main.py                    # App entry point, health endpoint, tag ordering
├── pyproject.toml             # Dependencies & project metadata
│
├── app/
│   ├── __init__.py
│   ├── api.py                 # Route definitions (routes only)
│   ├── catalog.py             # Scraper metadata for discovery endpoint
│   ├── helpers.py             # Shared request handler & error responses
│   ├── schemas.py             # APIResponse & APIError models
│   ├── services.py            # 12 service methods (one per scraper)
│   │
│   └── scrapers/              # Original scripts (untouched)
│       ├── __init__.py
│       ├── source_01_ists_consultation_meeting_scrapr.py
│       ├── source_02_ists_joint_coordination_meeting_scraper.py
│       ├── source_03_regenerators_scraper.py
│       ├── source_04_reallocation_meetings_scraper.py
│       ├── source_05_bidding_calender_scraper.py
│       ├── source_06_transmission_reports_scraper.py
│       ├── source_07_ctuil_compliance_fc_scraper.py
│       ├── source_08_monitoring_connectivity_scraper.py
│       ├── source_09_renewable_energy_scraper.py
│       ├── source_10a_potential_rezones_scraper.py
│       ├── source_10b_nct_meetings_scraper.py
│       └── source_11_substation_bulk_consumers_scraper.py
│
└── uploads/                   # All downloaded PDFs (auto-created)
    ├── ists_consultation_meeting/
    ├── ists_joint_coordination_meeting/
    ├── Effective_Date_Wise/
    ├── reallocation_meetings/
    ├── bidding_calendar/
    ├── compliance_and_fc/
    ├── revocations/
    ├── renewable_energy/
    ├── ctuil_bulk_consumers/
    ├── transmission_reports/
    ├── cea_500gw/
    └── cea_nct_minutes/
```

## Tech Stack

- **FastAPI** — REST framework
- **Playwright** — Browser automation for JS-rendered pages
- **aiohttp** — Async HTTP downloads
- **BeautifulSoup4** — HTML parsing
- **requests** — Sync HTTP calls (CEA scraper)
- **uv** — Dependency management
