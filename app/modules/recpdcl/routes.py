"""
RECPDCL scraper routes — 1 endpoint.
"""

from fastapi import APIRouter, Form

from app.helpers import ERROR_RESPONSES, handle_scraper
from app.schemas import APIResponse
from app.modules.recpdcl.services import RecpdclScraperService

router = APIRouter(tags=["RECPDCL Scrapers"])


@router.post(
    "/scrape/recpdcl-tender",
    response_model=APIResponse,
    summary="Scrape RECPDCL Tender PDFs",
    description=(
        "Searches the RECPDCL tender listing for entries whose title contains "
        "the given **query** substring, then downloads all matched PDFs filtered by "
        "keyword: *Corrigendum, Extension, Successful, RFP, Postponement, Qualified, Amendment*. "
        "Files are saved to `uploads/RECPDCL-RECTPCL-TENDER/<folder>/`."
    ),
    responses=ERROR_RESPONSES,
)
def scrape_recpdcl_tender(
    query: str = Form(..., description="Substring of the tender title to search for"),
):
    return handle_scraper(
        service_fn=lambda: RecpdclScraperService.run_recpdcl_tender(query=query),
        success_message="RECPDCL Tender scraper completed successfully.",
        error_message="RECPDCL Tender scraper failed.",
        error_code="RECPDCL_TENDER_ERROR",
    )
