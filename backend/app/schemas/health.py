"""Response schemas for system health endpoints."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response returned by the basic API availability endpoint."""

    status: str


class DatabaseHealthResponse(HealthResponse):
    """Response returned after a database connectivity check."""

    database: str
