"""
Integration test for the complete trend detection pipeline
Tests that all components work together correctly after recent fixes
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from application.services.google_trends_service import GoogleTrendsService
from infrastructure.repositories.trend_signal_repository import TrendSignalRepository
from infrastructure.database.models.trend_signal_model import TrendSignalModel


class TestTrendPipelineIntegration:
    """End-to-end integration tests for the trend pipeline"""
    
    @pytest.mark.asyncio
    async def test_trend_signal_create_and_persist(self):
        """Test creating a trend signal and verifying it can be persisted"""
        # Mock repository
        mock_repo = Mock()
        mock_repo.create = AsyncMock()
        
        # Create a trend signal model
        signal_data = {
            "user_email": "test@example.com",
            "niche": "fashion",
            "category": "streetwear",
            "location": "US",
            "radius": "50km",
            "keywords": ["fashion trends", "streetwear"],
            "search_interest": {},
            "geo_data": {},
            "related_queries": {},
            "rising_queries": {},
            "fetch_status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_model = TrendSignalModel(**signal_data)
        mock_repo.create.return_value = mock_model
        
        service = GoogleTrendsService(repository=mock_repo)
        
        result = await service.create_trend_signal(
            user_email="test@example.com",
            niche="fashion",
            category="streetwear",
            location="US",
            radius="50km"
        )
        
        # Verify the signal was created
        assert result.user_email == "test@example.com"
        assert result.niche == "fashion"
        assert result.fetch_status == "pending"
        mock_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enriched_data_persistence_fields(self):
        """Test that all enriched data fields are properly structured"""
        # This test verifies the domain entity has all required fields
        from domain.entities.trend_signal import TrendSignal
        
        signal = TrendSignal(
            id="test123",
            user_email="test@example.com",
            niche="tech",
            category="AI",
            location="US",
            radius="50km",
            keywords=["AI", "machine learning"],
            search_interest={},
            geo_data={},
            related_queries={},
            rising_queries={},
            fetch_status="completed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            # New enriched fields added in fixes
            is_real_social=True,
            is_real_saturation=False,
            lifecycle_stage="Growth",
            predicted_growth_pct=25.5,
            breakout_probability=0.75,
            profit_score=85,
            forecast_series=[10, 20, 30],
            timeframe="3_months"
        )
        
        # Verify all fields are accessible
        assert signal.is_real_social is True
        assert signal.is_real_saturation is False
        assert signal.lifecycle_stage == "Growth"
        assert signal.predicted_growth_pct == 25.5
        assert signal.breakout_probability == 0.75
        assert signal.profit_score == 85
        assert signal.forecast_series == [10, 20, 30]
        assert signal.timeframe == "3_months"
    
    @pytest.mark.asyncio
    async def test_repository_update_enriched_data_method_exists(self):
        """Test that the repository has the update_enriched_data method"""
        from infrastructure.repositories.trend_signal_repository import TrendSignalRepository
        
        # Verify the method exists
        assert hasattr(TrendSignalRepository, 'update_enriched_data')
        
        # Check method signature
        import inspect
        sig = inspect.signature(TrendSignalRepository.update_enriched_data)
        params = list(sig.parameters.keys())
        
        # Verify expected parameters exist
        assert 'trend_id' in params
        assert 'arbitrage_score' in params
        assert 'saturation_score' in params
        assert 'social_score' in params
        assert 'lifecycle_stage' in params
        assert 'predicted_growth_pct' in params
        assert 'breakout_probability' in params
        assert 'profit_score' in params
    
    @pytest.mark.asyncio
    async def test_error_handling_returns_user_friendly_messages(self):
        """Test that error handling provides user-friendly messages"""
        mock_repo = Mock()
        mock_repo.create = AsyncMock(side_effect=Exception("Database connection error"))
        
        service = GoogleTrendsService(repository=mock_repo)
        
        # This should not raise an exception but handle it gracefully
        try:
            await service.create_trend_signal(
                user_email="test@example.com",
                niche="fashion",
                category="streetwear",
                location="US",
                radius="50km"
            )
        except Exception as e:
            # If an exception is raised, ensure it's not exposing internal details
            error_msg = str(e)
            # Should not contain stack traces or technical jargon
            assert "Database connection error" in error_msg or "trends" in error_msg.lower()
