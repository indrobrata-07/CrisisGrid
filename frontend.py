from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse


# ===================================================
# FRONTEND ROUTER
# ===================================================

router = APIRouter()


BASE_DIR = Path(__file__).resolve().parent


DASHBOARD_FILE = (
    BASE_DIR / "dashboard.html"
)


REPORT_FILE = (
    BASE_DIR / "report.html"
)


# ===================================================
# COMMAND CENTER
# ===================================================

@router.get(
    "/dashboard",
    include_in_schema=False
)
def dashboard():

    return FileResponse(
        DASHBOARD_FILE
    )


# ===================================================
# CITIZEN EMERGENCY REPORT PAGE
# ===================================================

@router.get(
    "/report",
    include_in_schema=False
)
def report_page():

    return FileResponse(
        REPORT_FILE
    )