# Unit Tests - Google Trends Service
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import pandas as pd

from application.services.google_trends_service import GoogleTrendsService
from domain.entities.trend_signal import TrendSignal


@pytest.fixture
def mock_repository():
    """Mock repository for testing"""
    repo = Mock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_latest_by_user = AsyncMock()
    repo.update_status = AsyncMock()
    repo.update_trend_data = AsyncMock()
    return repo


@pytest.fixture
def trends_service(mock_repository):
    """Create GoogleTrendsService with mocked repository"""
    return GoogleTrendsService(repository=mock_repository)


@pytest.fixture
def sample_trend_signal():
    """Sample trend signal for testing"""
    return TrendSignal(
        id="507f1f77bcf86cd799439011",
        user_email="test@example.com",
        niche="fashion",
        category="streetwear",
        location="US",
        radius="50km",
        keywords=["fashion trends", "clothing styles"],
        search_interest={},
        geo_data={},
        related_queries={},
        rising_queries={},
        fetch_status="pending",
        error_message=None,
        fetched_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestGoogleTrendsService:
    """Test suite for GoogleTrendsService"""
    
    @pytest.mark.asyncio
    async def test_get_keywords_for_niche(self, trends_service):
        """Test keyword generation for different niches"""
        # Test fashion niche
        keywords = trends_service._get_keywords_for_niche("fashion", "streetwear")
        assert "streetwear" in keywords
        assert len(keywords) <= 5
        
        # Test unknown niche
        keywords = trends_service._get_keywords_for_niche("unknown_niche", "category")
        assert "category" in keywords
    
    @pytest.mark.asyncio
    async def test_create_trend_signal(self, trends_service, mock_repository, sample_trend_signal):
        """Test creating a new trend signal"""
        mock_repository.create.return_value = sample_trend_signal
        
        result = await trends_service.create_trend_signal(
            user_email="test@example.com",
            niche="fashion",
            category="streetwear",
            location="US",
            radius="50km"
        )
        
        assert result.user_email == "test@example.com"
        assert result.niche == "fashion"
        assert result.category == "streetwear"
        assert result.fetch_status == "pending"
        mock_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_latest_trends(self, trends_service, mock_repository, sample_trend_signal):
        """Test retrieving latest trends for a user"""
        mock_repository.get_latest_by_user.return_value = [sample_trend_signal]
        
        results = await trends_service.get_latest_trends("test@example.com", limit=10)
        
        assert len(results) == 1
        assert results[0].user_email == "test@example.com"
        mock_repository.get_latest_by_user.assert_called_once_with("test@example.com", 10)
    
    @pytest.mark.asyncio
    async def test_get_trend_by_id(self, trends_service, mock_repository, sample_trend_signal):
        """Test retrieving a specific trend by ID"""
        mock_repository.get_by_id.return_value = sample_trend_signal
        
        result = await trends_service.get_trend_by_id("507f1f77bcf86cd799439011")
        
        assert result.id == "507f1f77bcf86cd799439011"
        assert result.niche == "fashion"
        mock_repository.get_by_id.assert_called_once_with("507f1f77bcf86cd799439011")
    
    @pytest.mark.asyncio
    async def test_fetch_trends_data_success(self, trends_service):
        """Test successful Google Trends data fetching"""
        # Mock PyTrends
        mock_pytrends = Mock()
        
        # Create sample DataFrames
        interest_over_time_df = pd.DataFrame({
            'fashion trends': [50, 60, 70],
            'clothing styles': [40, 50, 60],
        }, index=pd.date_range('2024-01-01', periods=3))
        
        interest_by_region_df = pd.DataFrame({
            'fashion trends': [80],
            'clothing styles': [70],
        }, index=['United States'])
        
        related_queries_dict = {
            'fashion trends': {
                'top': pd.DataFrame({'query': ['trend 1'], 'value': [100]}),
                'rising': pd.DataFrame({'query': ['rising 1'], 'value': [200]})
            }
        }
        
        mock_pytrends.interest_over_time.return_value = interest_over_time_df
        mock_pytrends.interest_by_region.return_value = interest_by_region_df
        mock_pytrends.related_queries.return_value = related_queries_dict
        
        with patch.object(trends_service, '_get_pytrends', return_value=mock_pytrends):
            result = await trends_service.fetch_trends_data(
                keywords=["fashion trends", "clothing styles"],
                location="US"
            )
        
        assert result["success"] is True
        assert result["keywords"] == ["fashion trends", "clothing styles"]
        assert "search_interest" in result
        assert "geo_data" in result
        assert "related_queries" in result
        assert "rising_queries" in result
    
    @pytest.mark.asyncio
    async def test_fetch_trends_data_failure(self, trends_service):
        """Test Google Trends data fetching with error"""
        mock_pytrends = Mock()
        mock_pytrends.build_payload.side_effect = Exception("API Error")
        
        with patch.object(trends_service, '_get_pytrends', return_value=mock_pytrends):
            result = await trends_service.fetch_trends_data(
                keywords=["fashion trends"],
                location="US"
            )
        
        assert result["success"] is False
        assert result["error"] is not None
        assert "API Error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_process_trend_signal_success(self, trends_service, mock_repository, sample_trend_signal):
        """Test successful trend signal processing"""
        mock_repository.get_by_id.return_value = sample_trend_signal
        mock_repository.update_status.return_value = True
        mock_repository.update_trend_data.return_value = True
        
        # Mock fetch_trends_data
        with patch.object(trends_service, 'fetch_trends_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "success": True,
                "keywords": ["fashion trends"],
                "search_interest": {},
                "geo_data": {},
                "related_queries": {},
                "rising_queries": {},
                "error": None
            }
            
            result = await trends_service.process_trend_signal("507f1f77bcf86cd799439011")
        
        assert result is True
        mock_repository.update_status.assert_called()
        mock_repository.update_trend_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_trend_signal_not_found(self, trends_service, mock_repository):
        """Test processing non-existent trend signal"""
        mock_repository.get_by_id.return_value = None
        
        result = await trends_service.process_trend_signal("invalid_id")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_process_trend_signal_fetch_failure(self, trends_service, mock_repository, sample_trend_signal):
        """Test trend signal processing with fetch failure"""
        mock_repository.get_by_id.return_value = sample_trend_signal
        mock_repository.update_status.return_value = True
        
        # Mock fetch_trends_data to return failure
        with patch.object(trends_service, 'fetch_trends_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                "success": False,
                "keywords": [],
                "search_interest": {},
                "geo_data": {},
                "related_queries": {},
                "rising_queries": {},
                "error": "API Error"
            }
            
            result = await trends_service.process_trend_signal("507f1f77bcf86cd799439011")
        
        assert result is False
        # Verify status was updated to failed
        calls = mock_repository.update_status.call_args_list
        assert any("failed" in str(call) for call in calls)


class TestNicheKeywordMapping:
    """Test niche-to-keyword mapping"""
    
    def test_all_niches_have_keywords(self):
        """Ensure all predefined niches have keyword mappings"""
        service = GoogleTrendsService()
        
        for niche in service.NICHE_KEYWORDS.keys():
            keywords = service._get_keywords_for_niche(niche, "")
            assert len(keywords) > 0
            assert len(keywords) <= 5
    
    def test_category_inclusion(self):
        """Test that category is included in keywords"""
        service = GoogleTrendsService()
        
        keywords = service._get_keywords_for_niche("fashion", "unique_category")
        assert "unique_category" in keywords
