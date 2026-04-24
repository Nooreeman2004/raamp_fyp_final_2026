# Presentation Layer - Business Domain Router
from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
from presentation.schemas.business_domain_schemas import (
    BusinessDomainResponse,
    BusinessDomainsListResponse
)
from infrastructure.database.models.business_domain_model import BusinessDomainModel
from presentation.utils.validation import validate_object_id
from presentation.schemas.error_response import ErrorResponse, ErrorCode

router = APIRouter(prefix="/business-domains", tags=["Business Domains"])

# Simple cache for static business domains (reduces DB queries)
_domains_cache: dict = {"data": None, "expires_at": None}


@router.get(
    "",
    response_model=BusinessDomainsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all business domains"
)
async def get_business_domains():
    """
    Get list of all available business domain categories.
    Used for populating dropdown in profile creation form.
    
    Cached for 24 hours since business domains rarely change.

    Returns:
    - List of business domains with id, business name, and description
    - Total count of available domains
    """
    # Check cache first
    now = datetime.utcnow()
    if _domains_cache["data"] and _domains_cache["expires_at"] and now < _domains_cache["expires_at"]:
        return _domains_cache["data"]
    
    # Cache miss - fetch from database
    domains = await BusinessDomainModel.find_all().to_list()

    domain_responses = [
        BusinessDomainResponse(
            id=str(domain.id),
            business=domain.business,
            description=domain.description
        )
        for domain in domains
    ]

    response = BusinessDomainsListResponse(
        domains=domain_responses,
        total=len(domain_responses)
    )
    
    # Update cache with 24-hour TTL
    _domains_cache["data"] = response
    _domains_cache["expires_at"] = now + timedelta(hours=24)
    
    return response


@router.get(
    "/{domain_id}",
    response_model=BusinessDomainResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single business domain by ID"
)
async def get_business_domain(domain_id: str):
    """
    Get a single business domain by its ObjectId.

    Args:
    - domain_id: MongoDB ObjectId as string

    Returns:
    - Business domain details
    """
    # Validate format using shared utility
    obj_id = validate_object_id(domain_id, "domain ID")

    domain = await BusinessDomainModel.get(obj_id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error_code=ErrorCode.NOT_FOUND,
                message="Business domain not found"
            ).model_dump()
        )

    return BusinessDomainResponse(
        id=str(domain.id),
        business=domain.business,
        description=domain.description
    )
