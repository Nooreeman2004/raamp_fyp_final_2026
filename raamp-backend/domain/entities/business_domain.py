# Domain Layer - Business Domain Entity
from dataclasses import dataclass
from typing import Optional


@dataclass
class BusinessDomain:
    """Business Domain entity - represents business category"""
    id: Optional[str]  # MongoDB ObjectId as string
    business: str
    description: str
