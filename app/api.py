"""
API routes - one endpoint per scraper module.
"""

from fastapi import APIRouter

from app.catalog import SCRAPER_CATALOG
from app.helpers import ERROR_RESPONSES, handle_scraper
from app.schemas import APIResponse
from app.services import ScraperService

router = APIRouter()


# ══════════════════════════════════════════════════════════════════
#  CTUIL Scrapers
# ══════════════════════════════════════════════════════════════════

@router.post(
    "/scrape/ists-consultation-meeting",
    response_model=APIResponse,
    tags=["CTUIL Scrapers"],
    summary="Scrape ISTS Consultation Meeting PDFs",
    description=(
        "Downloads **Agenda** and **Minutes** PDFs for all five regions "
        "(NR, WR, SR, ER, NER) from the CTUIL ISTS Consultation Meeting page."
    ),
    responses=ERROR_RESPONSES,
)
def scrape_ists_consultation_meeting():
    return handle_scraper(
        service_fn=ScraperService.run_ists_consultation_meeting,
        success_message="ISTS Consultation Meeting scraper completed successfully.",
        error_message="ISTS Consultation Meeting scraper failed.",
        error_code="ISTS_CONSULTATION_MEETING_ERROR",
    )


@router.post(
    "/scrape/ists-joint-coordination-meeting",
    response_model=APIResponse,
    tags=["CTUIL Scrapers"],
    summary="Scrape ISTS Joint Coordination Meeting PDFs",
    description=(
        "Downloads **Notice** and **Minutes** PDFs for all regions from "
        "the CTUIL ISTS Joint Coordination Meeting page."
    ),
    responses=ERROR_RESPONSES,
)
def scrape_ists_joint_coordination_meeting():
    return handle_scraper(
        service_fn=ScraperService.run_ists_joint_coordination_meeting,
        success_message="ISTS Joint Coordination Meeting scraper completed successfully.",
        error_message="ISTS Joint Coordination Meeting scraper failed.",
        error_code="ISTS_JOINT_COORDINATION_MEETING_ERROR",
    )


@router.post(
    "/scrape/regenerators",
    response_model=APIResponse,
    tags=["CTUIL Scrapers"],
    summary="Scrape RE Generators PDFs",
    description=(
        "Downloads effective-date-wise connectivity PDFs for RE Generators "
        "from the CTUIL regenerators page (Playwright-rendered)."
    ),
    responses=ERROR_RESPONSES,
)
def scrape_regenerators():
    return handle_scraper(
        service_fn=ScraperService.run_regenerators,
        success_message="RE Generators scraper completed successfully.",
        error_message="RE Generators scraper failed.",
        error_code="REGENERATORS_ERROR",
    )


@router.post(
    "/scrape/reallocation-meetings",
    response_model=APIResponse,
    tags=["CTUIL Scrapers"],
    summary="Scrape Reallocation Meeting PDFs",
    description=(
        "Downloads **Agenda** and **Minutes** PDFs for all regions from "
        "the CTUIL Reallocation Meetings page (Playwright-rendered)."
    ),
    responses=ERROR_RESPONSES,
)
def scrape_reallocation_meetings():
    return handle_scraper(
        service_fn=ScraperService.run_reallocation_meetings,
        success_message="Reallocation Meetings scraper completed successfully.",
        error_message="Reallocation Meetings scraper failed.",
        error_code="REALLOCATION_MEETINGS_ERROR",
    )


@router.post(
    "/scrape/bidding-calendar",
    response_model=APIResponse,
    tags=["CTUIL Scrapers"],
    summary="Scrape Bidding Calendar PDFs",
    description="Downloads Bidding Calendar PDFs from the CTUIL website.",
    responses=ERROR_RESPONSES,
)
def scrape_bidding_calendar():
    return handle_scraper(
        service_fn=ScraperService.run_bidding_calendar,
        success_message="Bidding Calendar scraper completed successfully.",
        error_message="Bidding Calendar scraper failed.",
        error_code="BIDDING_CALENDAR_ERROR",
    )


@router.post(
    "/scrape/compliance-fc",
    response_model=APIResponse,
    tags=["CTUIL Scrapers"],
    summary="Scrape Compliance & FC PDFs",
    description=(
        "Downloads **Connectivity Grantee** PDFs from the CTUIL "
        "Compliance & FC page."
    ),
    responses=ERROR_RESPONSES,
)
def scrape_compliance_fc():
    return handle_scraper(
        service_fn=ScraperService.run_compliance_fc,
        success_message="Compliance & FC scraper completed successfully.",
        error_message="Compliance & FC scraper failed.",
        error_code="COMPLIANCE_FC_ERROR",
    )


@router.post(
    "/scrape/monitoring-connectivity",
    response_model=APIResponse,
    tags=["CTUIL Scrapers"],
    summary="Scrape Monitoring / Revocations PDFs",
    description="Downloads Monitoring and Revocation PDFs from the CTUIL page.",
    responses=ERROR_RESPONSES,
)
def scrape_monitoring_connectivity():
    return handle_scraper(
        service_fn=ScraperService.run_monitoring_connectivity,
        success_message="Monitoring / Revocations scraper completed successfully.",
        error_message="Monitoring / Revocations scraper failed.",
        error_code="MONITORING_CONNECTIVITY_ERROR",
    )


@router.post(
    "/scrape/renewable-energy",
    response_model=APIResponse,
    tags=["CTUIL Scrapers"],
    summary="Scrape Renewable Energy PDFs",
    description=(
        "Downloads RE margin PDFs (Non-RE, RE Substations, Proposed RE) "
        "and Bays Allocation PDFs from the CTUIL renewable-energy page."
    ),
    responses=ERROR_RESPONSES,
)
def scrape_renewable_energy():
    return handle_scraper(
        service_fn=ScraperService.run_renewable_energy,
        success_message="Renewable Energy scraper completed successfully.",
        error_message="Renewable Energy scraper failed.",
        error_code="RENEWABLE_ENERGY_ERROR",
    )


@router.post(
    "/scrape/substation-bulk-consumers",
    response_model=APIResponse,
    tags=["CTUIL Scrapers"],
    summary="Scrape Substation Bulk Consumer PDFs",
    description=(
        "Downloads Bulk Consumer PDFs from the CTUIL Substation page "
        "(Playwright-rendered)."
    ),
    responses=ERROR_RESPONSES,
)
def scrape_substation_bulk_consumers():
    return handle_scraper(
        service_fn=ScraperService.run_substation_bulk_consumers,
        success_message="Substation Bulk Consumers scraper completed successfully.",
        error_message="Substation Bulk Consumers scraper failed.",
        error_code="SUBSTATION_BULK_CONSUMERS_ERROR",
    )


# ══════════════════════════════════════════════════════════════════
#  CEA Scrapers
# ══════════════════════════════════════════════════════════════════

@router.post(
    "/scrape/transmission-reports",
    response_model=APIResponse,
    tags=["CEA Scrapers"],
    summary="Scrape CEA Transmission Reports",
    description=(
        "Downloads RTM and TBCB Transmission Reports from CEA for the "
        "last 24 months.  This is a **long-running** scraper."
    ),
    responses=ERROR_RESPONSES,
)
def scrape_transmission_reports():
    return handle_scraper(
        service_fn=ScraperService.run_transmission_reports,
        success_message="CEA Transmission Reports scraper completed successfully.",
        error_message="CEA Transmission Reports scraper failed.",
        error_code="TRANSMISSION_REPORTS_ERROR",
    )


@router.post(
    "/scrape/potential-re-zones",
    response_model=APIResponse,
    tags=["CEA Scrapers"],
    summary="Scrape 500 GW RE Integration PDFs",
    description=(
        "Downloads Transmission System PDFs for 500 GW Non-Fossil "
        "Capacity integration from the CEA website (Playwright-rendered)."
    ),
    responses=ERROR_RESPONSES,
)
def scrape_potential_re_zones():
    return handle_scraper(
        service_fn=ScraperService.run_potential_re_zones,
        success_message="500 GW RE Integration scraper completed successfully.",
        error_message="500 GW RE Integration scraper failed.",
        error_code="POTENTIAL_RE_ZONES_ERROR",
    )


@router.post(
    "/scrape/nct-meetings",
    response_model=APIResponse,
    tags=["CEA Scrapers"],
    summary="Scrape NCT Meeting Minutes",
    description=(
        "Downloads National Committee on Transmission meeting minutes "
        "PDFs from the CEA website (Playwright-rendered)."
    ),
    responses=ERROR_RESPONSES,
)
def scrape_nct_meetings():
    return handle_scraper(
        service_fn=ScraperService.run_nct_meetings,
        success_message="NCT Meeting Minutes scraper completed successfully.",
        error_message="NCT Meeting Minutes scraper failed.",
        error_code="NCT_MEETINGS_ERROR",
    )


# ══════════════════════════════════════════════════════════════════
#  API Info
# ══════════════════════════════════════════════════════════════════

@router.get(
    "/scrapers",
    response_model=APIResponse,
    tags=["API Info"],
    summary="List all available scrapers",
    description="Returns metadata for every registered scraper endpoint.",
)
def list_scrapers():
    return APIResponse.success(
        message=f"{len(SCRAPER_CATALOG)} scrapers available.",
        data={"scrapers": SCRAPER_CATALOG},
    )