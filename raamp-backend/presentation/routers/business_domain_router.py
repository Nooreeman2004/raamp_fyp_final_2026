# Presentation Layer - Business Domain Router
from fastapi import APIRouter, status
from presentation.schemas.business_domain_schemas import (
    BusinessDomainResponse,
    BusinessDomainsListResponse
)
from infrastructure.database.models.business_domain_model import BusinessDomainModel

router = APIRouter(prefix="/business-domains", tags=["Business Domains"])


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
    
    Returns:
    - List of business domains with id, business name, and description
    - Total count of available domains
    """
    domains = await BusinessDomainModel.find_all().to_list()
    
    domain_responses = [
        BusinessDomainResponse(
            id=str(domain.id),
            business=domain.business,
            description=domain.description
        )
        for domain in domains
    ]
    
    return BusinessDomainsListResponse(
        domains=domain_responses,
        total=len(domain_responses)
    )


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
    from bson import ObjectId
    from fastapi import HTTPException
    
    try:
        domain = await BusinessDomainModel.get(ObjectId(domain_id))
        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business domain not found"
            )
        
        return BusinessDomainResponse(
            id=str(domain.id),
            business=domain.business,
            description=domain.description
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid domain ID format",
        )
