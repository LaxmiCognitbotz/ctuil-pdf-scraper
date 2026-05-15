"""
Service layer — RECPDCL scraper module.
"""

import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class RecpdclScraperService:
    """
    Orchestrates execution of the RECPDCL tender scraper.
    """

    @staticmethod
    def run_recpdcl_tender(query: str) -> dict:
        """
        Source 10c — RECPDCL Tender Scraper
        ────────────────────────────────────────
        Searches the RECPDCL tender page for entries whose title contains
        the given query substring, then downloads all matched PDFs
        (filtered by keyword: Corrigendum, Extension, Successful, RFP,
        Postponement, Qualified, Amendment).

        Target : https://www.recpdcl.in/rectpcltender
        Output : uploads/RECPDCL-RECTPCL-TENDER/<folder_derived_from_query>/
        """
        from app.scrapers import source_10c_recpdcl_tender_scraper as script

        label = "RECPDCL Tender"
        logger.info("[START] %s  (query=%r)", label, query)
        start = time.time()

        output_dir = "uploads/RECPDCL-RECTPCL-TENDER"
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        script.run(user_input=query, output_dir=out_path)

        elapsed = round(time.time() - start, 2)
        logger.info("[DONE]  %s  completed in %ss", label, elapsed)

        folder_name = script.make_folder_name(query)
        return {
            "script": "source_10c_recpdcl_tender_scraper",
            "query": query,
            "execution_time_seconds": elapsed,
            "output_dir": str(out_path / folder_name).replace("\\", "/"),
        }
