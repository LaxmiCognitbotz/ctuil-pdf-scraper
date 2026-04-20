"""
Catalog - metadata for all registered scrapers.

Used by the API Info endpoint and the health check.
"""

SCRAPER_CATALOG = [
    {
        "endpoint": "/api/v1/scrape/ists-consultation-meeting",
        "label": "ISTS Consultation Meeting",
        "source": "CTUIL",
        "output_dir": "uploads/ists_consultation_meeting",
    },
    {
        "endpoint": "/api/v1/scrape/ists-joint-coordination-meeting",
        "label": "ISTS Joint Coordination Meeting",
        "source": "CTUIL",
        "output_dir": "uploads/ists_joint_coordination_meeting",
    },
    {
        "endpoint": "/api/v1/scrape/regenerators",
        "label": "RE Generators",
        "source": "CTUIL",
        "output_dir": "uploads/Effective_Date_Wise",
    },
    {
        "endpoint": "/api/v1/scrape/reallocation-meetings",
        "label": "Reallocation Meetings",
        "source": "CTUIL",
        "output_dir": "uploads/reallocation_meetings",
    },
    {
        "endpoint": "/api/v1/scrape/bidding-calendar",
        "label": "Bidding Calendar",
        "source": "CTUIL",
        "output_dir": "uploads/bidding_calendar",
    },
    {
        "endpoint": "/api/v1/scrape/compliance-fc",
        "label": "Compliance & FC",
        "source": "CTUIL",
        "output_dir": "uploads/compliance_and_fc",
    },
    {
        "endpoint": "/api/v1/scrape/monitoring-connectivity",
        "label": "Monitoring / Revocations",
        "source": "CTUIL",
        "output_dir": "uploads/revocations",
    },
    {
        "endpoint": "/api/v1/scrape/renewable-energy",
        "label": "Renewable Energy",
        "source": "CTUIL",
        "output_dir": "uploads/renewable_energy",
    },
    {
        "endpoint": "/api/v1/scrape/substation-bulk-consumers",
        "label": "Substation Bulk Consumers",
        "source": "CTUIL",
        "output_dir": "uploads/ctuil_bulk_consumers",
    },
    {
        "endpoint": "/api/v1/scrape/transmission-reports",
        "label": "CEA Transmission Reports",
        "source": "CEA",
        "output_dir": "uploads/transmission_reports",
    },
    {
        "endpoint": "/api/v1/scrape/potential-re-zones",
        "label": "500 GW RE Integration",
        "source": "CEA",
        "output_dir": "uploads/cea_500gw",
    },
    {
        "endpoint": "/api/v1/scrape/nct-meetings",
        "label": "NCT Meeting Minutes",
        "source": "CEA",
        "output_dir": "uploads/cea_nct_minutes",
    },
]
