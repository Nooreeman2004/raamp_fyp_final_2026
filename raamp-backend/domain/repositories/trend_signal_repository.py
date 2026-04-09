# Domain Layer - Trend Signal Repository Interface
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.trend_signal import TrendSignal


class ITrendSignalRepository(ABC):
    """Repository interface for Trend Signal operations"""
    
    @abstractmethod
    async def create(self, trend_signal: TrendSignal) -> TrendSignal:
        """Create a new trend signal record"""
        pass
    
    @abstractmethod
    async def get_by_id(self, trend_id: str) -> Optional[TrendSignal]:
        """Get a trend signal by ID"""
        pass
    
    @abstractmethod
    async def get_latest_by_user(self, user_email: str, limit: int = 10) -> List[TrendSignal]:
        """Get latest trend signals for a user"""
        pass
    
    @abstractmethod
    async def get_by_niche_and_location(
        self, 
        niche: str, 
        location: str, 
        limit: int = 10
    ) -> List[TrendSignal]:
        """Get trend signals by niche and location"""
        pass
    
    @abstractmethod
    async def update_status(
        self, 
        trend_id: str, 
        status: str, 
        error_message: Optional[str] = None,
        progress_step: Optional[str] = None
    ) -> bool:
        """Update the fetch status and progress step of a trend signal"""
        pass
    
    @abstractmethod
    async def update_trend_data(
        self,
        trend_id: str,
        keywords: List[str],
        search_interest: dict,
        geo_data: dict,
        related_queries: dict,
        rising_queries: dict,
        provider: Optional[str] = None,
        fallback_from: Optional[str] = None,
        geo_relaxed: Optional[bool] = None,
    ) -> bool:
        """Update trend signal with fetched Google Trends data"""
        pass
