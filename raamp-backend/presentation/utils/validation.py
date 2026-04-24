"""
Shared validation utilities for API routers.
"""
from fastapi import HTTPException, status
from bson import ObjectId


def validate_object_id(id_str: str, field_name: str = "ID") -> ObjectId:
    """
    Validate that a string is a proper MongoDB ObjectId.
    Raises HTTP 400 with a clear message if the format is invalid.
    """
    if not id_str:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} is required."
        )
    if not ObjectId.is_valid(id_str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format. Expected a 24-character hex string."
        )
    return ObjectId(id_str)
