import logging
import uvicorn
from fastapi import FastAPI
from app.api import router
from app.catalog import SCRAPER_CATALOG
from app.schemas import APIResponse

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── Tag ordering for Swagger UI ───────────────────────────────────
openapi_tags = [
    {
        "name": "Health",
        "description": "Server health and status checks.",
    },
    {
        "name": "API Info",
        "description": "Discover available scrapers and their endpoints.",
    },
    {
        "name": "CTUIL Scrapers",
        "description": "Scrapers targeting the CTUIL website (ctuil.in).",
    },
    {
        "name": "CEA Scrapers",
        "description": "Scrapers targeting the CEA website (cea.nic.in).",
    },
]

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title="CTUIL / CEA Scraper API",
    description=(
        "REST API wrapping all PDF scraper modules. "
    ),
    version="2.0.0",
    openapi_tags=openapi_tags,
)

# Health endpoint — registered FIRST so it appears at the top
@app.get("/", tags=["Health"], response_model=APIResponse, summary="Health Check")
def health():
    """Server health-check and status endpoint."""
    return APIResponse.success(
        message="Scraper API is running. Visit /docs for documentation.",
        data={"available_scrapers": len(SCRAPER_CATALOG)},
    )

# Include all scraper routes
app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
