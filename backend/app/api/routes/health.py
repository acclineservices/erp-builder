"""Application health endpoint."""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Check API availability")
def get_health() -> HealthResponse:
    """Confirm that the backend API process is running."""
    return HealthResponse(status="ok")
