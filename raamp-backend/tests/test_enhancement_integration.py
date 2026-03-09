"""
Test script to verify enhancement pipeline integration
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_service_imports():
    """Test that all enhancement services can be imported"""
    print("Testing service imports...")
    
    from application.services.lifecycle_classification_service import LifecycleClassificationService
    from application.services.trend_prediction_service import TrendPredictionService
    from application.services.profit_proxy_service import ProfitProxyService
    from application.services.trend_content_suggestion_service import TrendContentSuggestionService
    from application.services.google_trends_service import GoogleTrendsService
    from application.services.trend_detection_service import TrendDetectionService
    
    print("✅ All services imported successfully")
    return True

def test_service_instantiation():
    """Test that all services can be instantiated"""
    print("\nTesting service instantiation...")
    
    from application.services.lifecycle_classification_service import LifecycleClassificationService
    from application.services.trend_prediction_service import TrendPredictionService
    from application.services.profit_proxy_service import ProfitProxyService
    from application.services.trend_content_suggestion_service import TrendContentSuggestionService
    
    lifecycle_service = LifecycleClassificationService()
    prediction_service = TrendPredictionService()
    profit_service = ProfitProxyService()
    content_service = TrendContentSuggestionService()
    
    print("✅ All services instantiated successfully")
    return True

def test_lifecycle_classification():
    """Test lifecycle classification service"""
    print("\nTesting lifecycle classification...")
    
    from application.services.lifecycle_classification_service import LifecycleClassificationService
    
    service = LifecycleClassificationService()
    
    # Test classify_lifecycle
    result = service.classify_lifecycle(
        z_score=3.5,
        short_term_slope=2.5,
        long_term_slope=1.8,
        acceleration=0.3,
        saturation_score=45.0,
        avg_volume=65.0,
        current_value=72.0
    )
    
    print(f"  Lifecycle Stage: {result}")
    assert result in ["Emerging", "Breakout", "Mainstream", "Saturated", "Declining"]
    print("✅ Lifecycle classification working correctly")
    return True

def test_prediction_service():
    """Test trend prediction service"""
    print("\nTesting trend prediction...")
    
    from application.services.trend_prediction_service import TrendPredictionService
    
    service = TrendPredictionService()
    
    # Test predict_trend with sample data
    sample_values = [45.0, 48.0, 52.0, 58.0, 62.0, 67.0, 73.0, 76.0, 80.0, 84.0]
    result = service.predict_trend(values=sample_values, forecast_days=7)
    
    print(f"  Forecast Series: {result['forecast_series'][:3]}...")
    print(f"  Predicted Growth: {result['predicted_growth_pct']:.1f}%")
    print(f"  Breakout Probability: {result['breakout_probability']:.1f}")
    
    assert "forecast_series" in result
    assert "predicted_growth_pct" in result
    assert "breakout_probability" in result
    print("✅ Trend prediction working correctly")
    return True

def test_profit_proxy_service():
    """Test profit proxy service"""
    print("\nTesting profit proxy calculation...")
    
    from application.services.profit_proxy_service import ProfitProxyService
    
    service = ProfitProxyService()
    
    # Test calculate_profit_score
    result = service.calculate_profit_score(
        arbitrage_score=85.0,
        social_score=72.0,
        saturation_score=45.0,
        breakout_probability=78.5,
        lifecycle_stage="Breakout"
    )
    
    print(f"  Profit Score: {result:.1f}/100")
    
    # Test tier classification
    tier = service.get_profit_tier(result)
    print(f"  Profit Tier: {tier}")
    
    assert 0 <= result <= 100
    print("✅ Profit proxy calculation working correctly")
    return True

def test_timeframe_conversion():
    """Test timeframe conversion"""
    print("\nTesting timeframe conversion...")
    
    from application.services.google_trends_service import GoogleTrendsService
    
    service = GoogleTrendsService()
    
    # Test timeframe mappings
    mappings = {
        "24h": "now 1-d",
        "7d": "now 7-d",
        "30d": "today 1-m",
        "90d": "today 3-m"
    }
    
    for user_tf, expected_google_tf in mappings.items():
        result = service.convert_timeframe_to_google_format(user_tf)
        print(f"  {user_tf} → {result}")
        assert result == expected_google_tf, f"Expected {expected_google_tf}, got {result}"
    
    print("✅ Timeframe conversion working correctly")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("RAAMP ENHANCEMENT PIPELINE - INTEGRATION TEST")
    print("=" * 60)
    
    tests = [
        test_service_imports,
        test_service_instantiation,
        test_lifecycle_classification,
        test_prediction_service,
        test_profit_proxy_service,
        test_timeframe_conversion
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed: {test.__name__}")
            print(f"   Error: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All integration tests PASSED!")
        print("✅ Enhancement pipeline is ready for deployment")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())
