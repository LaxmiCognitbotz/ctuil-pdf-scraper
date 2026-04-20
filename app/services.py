"""
Service layer - one explicit method per scrapers/ module.
"""

import asyncio
import inspect
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


def _execute(script_module: Any, label: str, output_dir: str) -> dict:
    is_async = asyncio.iscoroutinefunction(script_module.main)
    script_name = script_module.__name__.rsplit(".", 1)[-1]

    logger.info("[START] %s  (module=%s, async=%s)", label, script_name, is_async)
    start = time.time()

    if is_async:
        asyncio.run(script_module.main())
    else:
        script_module.main()

    elapsed = round(time.time() - start, 2)
    logger.info("[DONE]  %s  completed in %ss", label, elapsed)

    return {
        "script": script_name,
        "execution_time_seconds": elapsed,
        "output_dir": output_dir,
    }


# ══════════════════════════════════════════════════════════════════
#  ScraperService
# ══════════════════════════════════════════════════════════════════

class ScraperService:
    """
    Orchestrates execution of all scrapers/ modules.

    Every public ``run_*`` method maps 1-to-1 to a script file.
    """

    # ──────────────────────────────────────────────────────────
    #  CTUIL Scrapers
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def run_ists_consultation_meeting() -> dict:
        """
        Source 01 — ISTS Consultation Meeting Scraper
        ──────────────────────────────────────────────
        Downloads **Agenda** and **Minutes** PDFs for all five regions
        (NR, WR, SR, ER, NER) across all paginated pages.

        Target : https://ctuil.in/ists-consultation-meeting
        Output : uploads/ists_consultation_meeting/{Region}/{Agenda|Minutes}/
        """
        from app.scrapers import source_01_ists_consultation_meeting_scrapr as script

        return _execute(
            script,
            label="ISTS Consultation Meeting",
            output_dir="uploads/ists_consultation_meeting",
        )

    @staticmethod
    def run_ists_joint_coordination_meeting() -> dict:
        """
        Source 02 — ISTS Joint Coordination Meeting Scraper
        ───────────────────────────────────────────────────
        Downloads **Notice** and **Minutes** PDFs for all regions.

        Target : https://ctuil.in/ists-joint-coordination-meeting
        Output : uploads/ists_joint_coordination_meeting/{Region}/{Notice|Minutes}/
        """
        from app.scrapers import source_02_ists_joint_coordination_meeting_scraper as script

        return _execute(
            script,
            label="ISTS Joint Coordination Meeting",
            output_dir="uploads/ists_joint_coordination_meeting",
        )

    @staticmethod
    def run_regenerators() -> dict:
        """
        Source 03 — RE Generators Scraper
        ─────────────────────────────────
        Downloads **effective-date-wise connectivity** PDFs.
        Uses Playwright to render the JS-heavy page.

        Target : https://ctuil.in/regenerators
        Output : uploads/Effective_Date_Wise/
        """
        from app.scrapers import source_03_regenerators_scraper as script

        return _execute(
            script,
            label="RE Generators",
            output_dir="uploads/Effective_Date_Wise",
        )

    @staticmethod
    def run_reallocation_meetings() -> dict:
        """
        Source 04 — Reallocation Meetings Scraper
        ──────────────────────────────────────────
        Downloads **Agenda** and **Minutes** PDFs for all regions.
        Uses Playwright to navigate region tabs.

        Target : https://www.ctuil.in/reallocation_meetings
        Output : uploads/reallocation_meetings/{Region}/{agenda|minutes}/
        """
        from app.scrapers import source_04_reallocation_meetings_scraper as script

        return _execute(
            script,
            label="Reallocation Meetings",
            output_dir="uploads/reallocation_meetings",
        )

    @staticmethod
    def run_bidding_calendar() -> dict:
        """
        Source 05 — Bidding Calendar Scraper
        ────────────────────────────────────
        Downloads Bidding Calendar PDFs from CTUIL.

        Target : https://www.ctuil.in/bidding-calendar
        Output : uploads/bidding_calendar/
        """
        from app.scrapers import source_05_bidding_calender_scraper as script

        return _execute(
            script,
            label="Bidding Calendar",
            output_dir="uploads/bidding_calendar",
        )

    @staticmethod
    def run_compliance_fc() -> dict:
        """
        Source 07 — Compliance & FC Scraper
        ───────────────────────────────────
        Downloads **Connectivity Grantee** PDFs.

        Target : https://ctuil.in/complianceandfc
        Output : uploads/compliance_and_fc/
        """
        from app.scrapers import source_07_ctuil_compliance_fc_scraper as script

        return _execute(
            script,
            label="Compliance & FC",
            output_dir="uploads/compliance_and_fc",
        )

    @staticmethod
    def run_monitoring_connectivity() -> dict:
        """
        Source 08 — Monitoring / Revocations Scraper
        ─────────────────────────────────────────────
        Downloads Monitoring and Revocation PDFs.

        Target : https://www.ctuil.in/revocations
        Output : uploads/revocations/
        """
        from app.scrapers import source_08_monitoring_connectivity_scraper as script

        return _execute(
            script,
            label="Monitoring / Revocations",
            output_dir="uploads/revocations",
        )

    @staticmethod
    def run_renewable_energy() -> dict:
        """
        Source 09 — Renewable Energy Scraper
        ────────────────────────────────────
        Downloads RE margin PDFs (Non-RE, RE Substations, Proposed RE)
        and Bays Allocation PDFs.  Uses Playwright.

        Target : https://www.ctuil.in/renewable-energy
        Output : uploads/renewable_energy/{bays_allocation|margin}/
        """
        from app.scrapers import source_09_renewable_energy_scraper as script

        return _execute(
            script,
            label="Renewable Energy",
            output_dir="uploads/renewable_energy",
        )

    @staticmethod
    def run_substation_bulk_consumers() -> dict:
        """
        Source 11 — Substation Bulk Consumers Scraper
        ──────────────────────────────────────────────
        Downloads Bulk Consumer PDFs.  Uses Playwright.

        Target : https://ctuil.in/substation-bulk-consumers
        Output : uploads/ctuil_bulk_consumers/
        """
        from app.scrapers import source_11_substation_bulk_consumers_scraper as script

        return _execute(
            script,
            label="Substation Bulk Consumers",
            output_dir="uploads/ctuil_bulk_consumers",
        )

    # ──────────────────────────────────────────────────────────
    #  CEA Scrapers
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def run_transmission_reports() -> dict:
        """
        Source 06 — CEA Transmission Reports Scraper  (SYNCHRONOUS)
        ────────────────────────────────────────────────────────────
        Downloads RTM and TBCB Transmission Reports for the last
        24 months using CEA's AJAX endpoint.

        Target : https://cea.nic.in/transmission-reports/?lang=en
        Output : uploads/transmission_reports/{year}/{month}/
        """
        from app.scrapers import source_06_transmission_reports_scraper as script

        return _execute(
            script,
            label="CEA Transmission Reports",
            output_dir="uploads/transmission_reports",
        )

    @staticmethod
    def run_potential_re_zones() -> dict:
        """
        Source 10a — 500 GW RE Integration Scraper
        ───────────────────────────────────────────
        Downloads Transmission System PDFs for 500 GW Non-Fossil
        Capacity integration.  Uses Playwright.

        Target : https://cea.nic.in/psp___a_i/transmission-system-for-integration-of-over-500-gw-non-fossil-capacity-by-2030/?lang=en
        Output : uploads/cea_500gw/
        """
        from app.scrapers import source_10a_potential_rezones_scraper as script

        return _execute(
            script,
            label="500 GW RE Integration",
            output_dir="uploads/cea_500gw",
        )

    @staticmethod
    def run_nct_meetings() -> dict:
        """
        Source 10b — NCT Meeting Minutes Scraper
        ─────────────────────────────────────────
        Downloads National Committee on Transmission meeting
        minutes PDFs from CEA.  Uses Playwright.

        Target : https://cea.nic.in/comm-trans/national-committee-on-transmission/?lang=en
        Output : uploads/cea_nct_minutes/
        """
        from app.scrapers import source_10b_nct_meetings_scraper as script

        return _execute(
            script,
            label="NCT Meeting Minutes",
            output_dir="uploads/cea_nct_minutes",
        )