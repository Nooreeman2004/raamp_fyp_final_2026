# Infrastructure Layer - Business Domain MongoDB Document
from beanie import Document
from pydantic import Field


class BusinessDomainModel(Document):
    """MongoDB document for BusinessDomain collection (Master/Lookup table)"""
    business: str = Field(..., description="Business category title (e.g., Fashion, Restaurants)")
    description: str = Field(..., description="Short explanation of what this category includes")
    
    class Settings:
        name = "business_domains"  # Collection name
        indexes = [
            "business",  # Index on business category for fast lookups
        ]
