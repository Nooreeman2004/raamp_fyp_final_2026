# Unit Tests - Trend Detection Engine
import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from infrastructure.utils.trend_math import TrendDetectionEngine
from domain.entities.trend_detection import TrendDetectionConfig, TrendSpike
from application.services.trend_detection_service import TrendDetectionService
from infrastructure.database.models.business_model import BusinessModel
from infrastructure.database.models.user_model import UserModel
from infrastructure.database.models.business_domain_model import BusinessDomainModel
from infrastructure.database.models.trend_detection_model import TrendDetectionModel


class TestTrendDetectionEngine:
    """Test suite for the mathematical detection logic"""
    
    def test_detect_spikes_flat_line(self):
        """Test with no spikes (constant value)"""
        dates = [f"2024-01-{i:02d}" for i in range(1, 21)]
        values = [50.0] * 20
        
        spikes = TrendDetectionEngine.detect_spikes(
            dates=dates,
            values=values,
            keyword="test",
            niche="tech",
            location="US"
        )
        
        assert len(spikes) == 0

    def test_detect_spikes_sudden_jump(self):
        """Test with a clear sudden jump at the end"""
        dates = [f"2024-01-{i:02d}" for i in range(1, 21)]
        # Flat baseline then huge spike
        values = [10.0] * 19 + [100.0]
        
        spikes = TrendDetectionEngine.detect_spikes(
            dates=dates,
            values=values,
            keyword="spike",
            niche="fashion",
            location="US",
            config=TrendDetectionConfig(threshold=1.5)
        )
        
        assert len(spikes) > 0
        assert spikes[0].keyword == "spike"
        assert spikes[0].current_value == 100.0

    def test_insufficient_data(self):
        """Test with too few data points"""
        dates = ["2024-01-01", "2024-01-02"]
        values = [10.0, 100.0] # Spike but not enough points
        
        spikes = TrendDetectionEngine.detect_spikes(
            dates=dates,
            values=values,
            keyword="test",
            niche="tech",
            location="US",
            config=TrendDetectionConfig(min_data_points=5)
        )
        
        assert len(spikes) == 0


class TestTrendDetectionService:
    """Test suite for the detection service orchestration"""

    @pytest.fixture
    def mock_deps(self):
        trends_service = Mock()
        notification_service = Mock()
        trends_service.create_trend_signal = AsyncMock()
        trends_service.process_trend_signal = AsyncMock()
        trends_service.get_trend_by_id = AsyncMock()
        notification_service.create_and_send = AsyncMock()
        
        return trends_service, notification_service

    @pytest.mark.asyncio
    async def test_run_detection_for_user_notifies_on_spike(self, mock_deps):
        """Test that the service triggers a notification when a spike is found"""
        trends_service, notification_service = mock_deps
        service = TrendDetectionService(trends_service, notification_service)
        
        # Mock User
        user = Mock()
        user.email = "user@example.com"
        user.business_domain = "507f1f77bcf86cd799439011"
        user.role = "Owner"
        
        # Mocking Beanie methods
        with patch.object(BusinessDomainModel, 'get', new_callable=AsyncMock) as mock_domain_get:
            mock_domain_get.return_value = Mock(business="Tech")
            
            # Mock BusinessModel.find_one
            mock_biz = Mock(country="US")
            m_find = Mock()
            m_find.return_value = AsyncMock(return_value=mock_biz)()
            
            with patch.object(BusinessModel, 'find_one', new_callable=Mock) as mock_find_one, \
                 patch.object(TrendDetectionModel, 'insert', new_callable=AsyncMock) as mock_insert:
                mock_find_one.return_value = AsyncMock(return_value=mock_biz)()
                
                # Mock Trend Data with a spike
                mock_trend = Mock()
                mock_trend.id = "trend_123"
                mock_trend.search_interest = {
                    "dates": [f"2024-01-{i:02d}" for i in range(1, 21)],
                    "data": {
                        "AI": [10.0] * 19 + [100.0]
                    }
                }
                
                trends_service.create_trend_signal.return_value = Mock(id="trend_123")
                trends_service.process_trend_signal.return_value = True
                trends_service.get_trend_by_id.return_value = mock_trend
                
                # Run the detection
                await service.run_detection_for_user(user)
                
                # Verify notification was sent
                assert notification_service.create_and_send.called
                args, kwargs = notification_service.create_and_send.call_args
                
                msg = kwargs.get("message", "")
                u_id = kwargs.get("user_id", "")
                meta = kwargs.get("metadata", {})
                
                assert "AI" in msg
                assert u_id == "user@example.com"
                assert meta.get("keyword") == "AI"

    @pytest.mark.asyncio
    async def test_run_detection_for_all_users(self, mock_deps):
        """Test that the service iterates through all users"""
        trends_service, notification_service = mock_deps
        service = TrendDetectionService(trends_service, notification_service)
        
        user1 = Mock(email="user1@example.com", business_domain="123")
        user2 = Mock(email="user2@example.com", business_domain="456")
        
        with patch.object(UserModel, 'find_all') as mock_find_all:
            mock_query = Mock()
            mock_query.to_list = AsyncMock(return_value=[user1, user2])
            mock_find_all.return_value = mock_query
            
            with patch.object(service, 'run_detection_for_user', new_callable=AsyncMock) as mock_run_user:
                await service.run_detection_for_all_users()
                assert mock_run_user.call_count == 2
