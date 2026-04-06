from fastapi import APIRouter
from app.services import DownloaderService
from app.schemas import APIResponse, APIError
from config.msg import msg

router = APIRouter()

@router.post("/download/margin", response_model=APIResponse, tags=["Download"])
def trigger_margin_download():
    """Download Renewable Energy connectivity margin PDFs from CTUIL."""
    try:
        response = DownloaderService.run_margin_downloader()
        return APIResponse(
            status=True, 
            message=msg["margin_download_success"], 
            data=response, 
            error=None
        )
    except Exception as e:
        return APIResponse(
            status=False, 
            message=msg["margin_download_failed"], 
            data=None, 
            error=APIError(code="MARGIN_ERROR", detail=str(e))
        )

@router.post("/download/minutes", response_model=APIResponse, tags=["Download"])
def trigger_minutes_download():
    """Download ISTS Northern Region consultation meeting minutes."""
    try:
        response = DownloaderService.run_minutes_downloader()
        return APIResponse(
            status=True, 
            message=msg["minutes_download_success"], 
            data=response, 
            error=None
        )
    except Exception as e:
        return APIResponse(
            status=False, 
            message=msg["minutes_download_failed"], 
            data=None, 
            error=APIError(code="MINUTES_ERROR", detail=str(e))
        )

@router.post("/download/rtm-tbcb", response_model=APIResponse, tags=["Download"])
def trigger_rtm_tbcb_download():
    """Download Northern Region RTM and TBCB PDFs from CTUIL."""
    try:
        response = DownloaderService.run_rtm_tbcb_downloader()
        return APIResponse(
            status=True, 
            message=msg["rtm_tbcb_download_success"], 
            data=response, 
            error=None
        )
    except Exception as e:
        return APIResponse(
            status=False, 
            message=msg["rtm_tbcb_download_failed"], 
            data=None, 
            error=APIError(code="RTM_TBCB_ERROR", detail=str(e))
        )
