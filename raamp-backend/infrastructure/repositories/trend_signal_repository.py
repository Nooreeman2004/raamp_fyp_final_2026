# Infrastructure Layer - Trend Signal Repository Implementation
from typing import Optional, List, Dict
from datetime import datetime
from bson import ObjectId

from domain.repositories.trend_signal_repository import ITrendSignalRepository
from domain.entities.trend_signal import TrendSignal
from infrastructure.database.models.trend_signal_model import TrendSignalModel


class TrendSignalRepository(ITrendSignalRepository):
    """MongoDB implementation of Trend Signal repository"""
    
    async def create(self, trend_signal: TrendSignal) -> TrendSignal:
        """Create a new trend signal record"""
        model = TrendSignalModel(
            user_email=trend_signal.user_email,
            niche=trend_signal.niche,
            category=trend_signal.category,
            location=trend_signal.location,
            radius=trend_signal.radius,
            keywords=trend_signal.keywords,
            search_interest=trend_signal.search_interest,
            geo_data=trend_signal.geo_data,
            related_queries=trend_signal.related_queries,
            rising_queries=trend_signal.rising_queries,
            fetch_status=trend_signal.fetch_status,
            error_message=trend_signal.error_message,
            fetched_at=trend_signal.fetched_at,
            created_at=trend_signal.created_at,
            updated_at=trend_signal.updated_at,
        )
        
        await model.insert()
        
        # Convert back to domain entity
        trend_signal.id = str(model.id)
        return trend_signal
    
    async def get_by_id(self, trend_id: str) -> Optional[TrendSignal]:
        """Get a trend signal by ID"""
        try:
            model = await TrendSignalModel.get(ObjectId(trend_id))
            if not model:
                return None
            
            return self._to_entity(model)
        except Exception:
            return None
    
    async def get_latest_by_user(self, user_email: str, limit: int = 10) -> List[TrendSignal]:
        """Get latest trend signals for a user"""
        models = await TrendSignalModel.find(
            TrendSignalModel.user_email == user_email
        ).sort(-TrendSignalModel.created_at).limit(limit).to_list()
        
        return [self._to_entity(model) for model in models]
    
    async def get_by_niche_and_location(
        self, 
        niche: str, 
        location: str, 
        limit: int = 10
    ) -> List[TrendSignal]:
        """Get trend signals by niche and location"""
        models = await TrendSignalModel.find(
            TrendSignalModel.niche == niche,
            TrendSignalModel.location == location,
            TrendSignalModel.fetch_status == "completed"
        ).sort(-TrendSignalModel.created_at).limit(limit).to_list()
        
        return [self._to_entity(model) for model in models]
    
    async def update_status(
        self, 
        trend_id: str, 
        status: str, 
        error_message: Optional[str] = None
    ) -> bool:
        """Update the fetch status of a trend signal"""
        try:
            model = await TrendSignalModel.get(ObjectId(trend_id))
            if not model:
                return False
            
            model.fetch_status = status
            model.error_message = error_message
            model.updated_at = datetime.utcnow()
            
            if status == "completed":
                model.fetched_at = datetime.utcnow()
            
            await model.save()
            return True
        except Exception:
            return False
    
    async def update_trend_data(
        self,
        trend_id: str,
        keywords: List[str],
        search_interest: dict,
        geo_data: dict,
        related_queries: dict,
        rising_queries: dict
    ) -> bool:
        """Update trend signal with fetched Google Trends data"""
        try:
            model = await TrendSignalModel.get(ObjectId(trend_id))
            if not model:
                return False
            
            model.keywords = keywords
            model.search_interest = search_interest
            model.geo_data = geo_data
            model.related_queries = related_queries
            model.rising_queries = rising_queries
            model.fetch_status = "completed"
            model.fetched_at = datetime.utcnow()
            model.updated_at = datetime.utcnow()
            
            await model.save()
            return True
        except Exception:
            return False
    
    async def update_enriched_data(
        self,
        trend_id: str,
        arbitrage_score: Optional[float] = None,
        saturation_score: Optional[float] = None,
        social_score: Optional[float] = None,
        hashtags: Optional[List[str]] = None,
        platform_bias: Optional[Dict[str, float]] = None,
        is_real_social: bool = False,
        is_real_saturation: bool = False,
        lifecycle_stage: Optional[str] = None,
        predicted_growth_pct: Optional[float] = None,
        breakout_probability: Optional[float] = None,
        profit_score: Optional[float] = None,
        forecast_series: Optional[List[float]] = None,
        timeframe: Optional[str] = None
    ) -> bool:
        """Update trend signal with all enriched analytics data"""
        try:
            model = await TrendSignalModel.get(ObjectId(trend_id))
            if not model:
                return False
            
            # Update all enriched fields
            if arbitrage_score is not None:
                model.arbitrage_score = arbitrage_score
            if saturation_score is not None:
                model.saturation_score = saturation_score
            if social_score is not None:
                model.social_score = social_score
            if hashtags is not None:
                model.hashtags = hashtags
            if platform_bias is not None:
                model.platform_bias = platform_bias
            model.is_real_social = is_real_social
            model.is_real_saturation = is_real_saturation
            
            # Update lifecycle and prediction fields
            if lifecycle_stage is not None:
                model.lifecycle_stage = lifecycle_stage
            if predicted_growth_pct is not None:
                model.predicted_growth_pct = predicted_growth_pct
            if breakout_probability is not None:
                model.breakout_probability = breakout_probability
            if profit_score is not None:
                model.profit_score = profit_score
            if forecast_series is not None:
                model.forecast_series = forecast_series
            if timeframe is not None:
                model.timeframe = timeframe
            
            model.updated_at = datetime.utcnow()
            await model.save()
            return True
        except Exception:
            return False
    
    def _to_entity(self, model: TrendSignalModel) -> TrendSignal:
        """Convert database model to domain entity"""
        return TrendSignal(
            id=str(model.id),
            user_email=model.user_email,
            niche=model.niche,
            category=model.category,
            location=model.location,
            radius=model.radius,
            keywords=model.keywords,
            search_interest=model.search_interest,
            geo_data=model.geo_data,
            related_queries=model.related_queries,
            rising_queries=model.rising_queries,
            arbitrage_score=model.arbitrage_score,
            saturation_score=model.saturation_score,
            social_score=model.social_score,
            hashtags=model.hashtags,
            platform_bias=model.platform_bias,
            is_real_social=model.is_real_social,
            is_real_saturation=model.is_real_saturation,
            lifecycle_stage=model.lifecycle_stage,
            predicted_growth_pct=model.predicted_growth_pct,
            breakout_probability=model.breakout_probability,
            profit_score=model.profit_score,
            forecast_series=model.forecast_series,
            timeframe=model.timeframe,
            fetch_status=model.fetch_status,
            error_message=model.error_message,
            fetched_at=model.fetched_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
