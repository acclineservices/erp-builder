"""Database connectivity health endpoint."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine
from app.schemas.health import DatabaseHealthResponse

router = APIRouter(prefix="/health", tags=["system"])


@router.get("/database", response_model=DatabaseHealthResponse, summary="Check database connectivity")
def get_database_health() -> DatabaseHealthResponse:
    """Confirm that the API can establish a PostgreSQL database connection."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connectivity is unavailable.",
        ) from exc
    return DatabaseHealthResponse(status="ok", database="available")
