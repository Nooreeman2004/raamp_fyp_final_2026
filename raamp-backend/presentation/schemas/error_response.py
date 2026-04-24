"""
Standardized error response schemas for all API routers.

Usage:
    from presentation.schemas.error_response import ErrorResponse, ErrorCode

    raise HTTPException(
        status_code=404,
        detail=ErrorResponse(
            error_code=ErrorCode.NOT_FOUND,
            message="The requested post was not found."
        ).model_dump()
    )
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime, timezone
from enum import Enum
import uuid


class ErrorCode(str, Enum):
    """Standardized machine-readable error codes for the frontend to act upon."""
    # Client errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_ID = "INVALID_ID"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"

    # Server errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    TIMEOUT = "TIMEOUT"

    # Domain-specific
    INSTAGRAM_API_ERROR = "INSTAGRAM_API_ERROR"
    FACEBOOK_API_ERROR = "FACEBOOK_API_ERROR"
    OPENAI_API_ERROR = "OPENAI_API_ERROR"
    SUBSCRIPTION_REQUIRED = "SUBSCRIPTION_REQUIRED"


class ErrorResponse(BaseModel):
    """
    Uniform error payload returned in all HTTPException detail fields.

    All routers should raise HTTPException with an ErrorResponse.model_dump()
    as the `detail` so that the frontend can reliably parse errors by error_code.
    """
    error_code: ErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-friendly error description")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional structured context (e.g., field-level validation errors)"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp of when the error occurred"
    )
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ID for tracing this request in logs"
    )


def validation_error(message: str, fields: Optional[Dict[str, str]] = None) -> Dict:
    """Convenience builder for validation errors."""
    return ErrorResponse(
        error_code=ErrorCode.VALIDATION_ERROR,
        message=message,
        details={"fields": fields} if fields else None
    ).model_dump()


def not_found_error(resource: str) -> Dict:
    """Convenience builder for 404 not found errors."""
    return ErrorResponse(
        error_code=ErrorCode.NOT_FOUND,
        message=f"{resource} was not found."
    ).model_dump()


def invalid_id_error(field_name: str = "ID") -> Dict:
    """Convenience builder for ObjectId / UUID format errors."""
    return ErrorResponse(
        error_code=ErrorCode.INVALID_ID,
        message=f"The provided {field_name} is not a valid format."
    ).model_dump()


def internal_error(message: str = "An unexpected error occurred. Please try again.") -> Dict:
    """Convenience builder for 500 internal server errors."""
    return ErrorResponse(
        error_code=ErrorCode.INTERNAL_ERROR,
        message=message
    ).model_dump()
