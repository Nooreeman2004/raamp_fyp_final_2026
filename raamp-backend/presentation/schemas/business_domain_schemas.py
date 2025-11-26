# Presentation Layer - Business Domain Schemas
from pydantic import BaseModel
from typing import List


class BusinessDomainResponse(BaseModel):
    """Response schema for a single business domain"""
    id: str
    business: str
    description: str
    
    model_config = {
        "from_attributes": True
    }


class BusinessDomainsListResponse(BaseModel):
    """Response schema for list of business domains"""
    domains: List[BusinessDomainResponse]
    total: int
