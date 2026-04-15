"""Shared API response envelopes."""

from pydantic import BaseModel, ConfigDict
from typing import Any, Optional


class APIResponse(BaseModel):
    """Standard API response envelope."""

    status: str
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "data": {"id": 1, "name": "example"},
                "error": None,
                "message": None,
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response."""

    status: str = "error"
    error: str
    message: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "error",
                "error": "unauthorized",
                "message": "Invalid or missing credentials",
            }
        }
    )
