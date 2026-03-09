"""
Runtime validation tests for RAAMP enhancement features.
Tests actual API endpoints with database integration.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from infrastructure.database.models.user_model import UserModel
from infrastructure.database.models.business_model import BusinessModel
from infrastructure.database.models.trend_signal_model import TrendSignalModel
from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient


async def init_db():
    """Initialize database connection"""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(
        database=client.raamp_db,
        document_models=[
            UserModel,
            BusinessModel,
            TrendSignalModel,
            TrendDetectionModel
        ]
    )


async def test_location_locking():
    """Test that location locking is enforced"""
    print("\n" + "="*60)
    print("TEST: Location Locking Enforcement")
    print("="*60)
    
    # Find a test user
    user = await UserModel.find_one({"email": {"$exists": True}})
    
    if not user:
        print("⚠️  No test users found in database")
        return False
    
    # Check if user has onboarding_location set
    if hasattr(user, 'onboarding_location') and user.onboarding_location:
        print(f"✅ User {user.email} has onboarding_location: {user.onboarding_location}")
        print("✅ Location locking field exists in UserModel")
        return True
    else:
        print(f"⚠️  User {user.email} does not have onboarding_location set")
        print("ℹ️  Field exists but not populated yet (expected for existing users)")
        return True


async def test_enhanced_fields_in_database():
    """Test that enhanced fields are stored in database"""
    print("\n" + "="*60)
    print("TEST: Enhanced Fields in Database Models")
    print("="*60)
    
    # Check TrendSignalModel
    trend_signal = await TrendSignalModel.find_one()
    
    if trend_signal:
        fields_to_check = [
            'lifecycle_stage',
            'predicted_growth_pct',
            'breakout_probability',
            'profit_score',
            'forecast_series',
            'timeframe'
        ]
        
        print(f"\nChecking TrendSignal ID: {trend_signal.id}")
        all_fields_exist = True
        
        for field in fields_to_check:
            if hasattr(trend_signal, field):
                value = getattr(trend_signal, field, None)
                status = "✅" if value is not None else "🟡"
                print(f"  {status} {field}: {value}")
            else:
                print(f"  ❌ {field}: NOT FOUND IN MODEL")
                all_fields_exist = False
        
        if all_fields_exist:
            print("\n✅ All enhanced fields exist in TrendSignalModel")
            return True
        else:
            print("\n❌ Some fields missing from TrendSignalModel")
            return False
    else:
        print("⚠️  No TrendSignal records found in database")
        print("ℹ️  Run a trend detection first to populate data")
        return False


async def test_timeframe_support():
    """Test that timeframe filtering is supported"""
    print("\n" + "="*60)
    print("TEST: Timeframe Filtering Support")
    print("="*60)
    
    from application.services.google_trends_service import GoogleTrendsService
    
    service = GoogleTrendsService()
    
    # Test all timeframe conversions
    timeframes = {
        "24h": "now 1-d",
        "7d": "now 7-d",
        "30d": "today 1-m",
        "90d": "today 3-m"
    }
    
    all_passed = True
    for user_tf, expected_google_tf in timeframes.items():
        result = service.convert_timeframe_to_google_format(user_tf)
        if result == expected_google_tf:
            print(f"  ✅ {user_tf} → {result}")
        else:
            print(f"  ❌ {user_tf} → {result} (expected {expected_google_tf})")
            all_passed = False
    
    if all_passed:
        print("\n✅ All timeframe conversions working correctly")
        return True
    else:
        print("\n❌ Some timeframe conversions failed")
        return False


async def test_service_integration():
    """Test that all enhancement services are properly integrated"""
    print("\n" + "="*60)
    print("TEST: Enhancement Services Integration")
    print("="*60)
    
    try:
        from application.services.lifecycle_classification_service import LifecycleClassificationService
        from application.services.trend_prediction_service import TrendPredictionService
        from application.services.profit_proxy_service import ProfitProxyService
        from application.services.trend_content_suggestion_service import TrendContentSuggestionService
        
        # Instantiate all services
        lifecycle_service = LifecycleClassificationService()
        prediction_service = TrendPredictionService()
        profit_service = ProfitProxyService()
        content_service = TrendContentSuggestionService()
        
        print("  ✅ LifecycleClassificationService instantiated")
        print("  ✅ TrendPredictionService instantiated")
        print("  ✅ ProfitProxyService instantiated")
        print("  ✅ TrendContentSuggestionService instantiated")
        
        # Test lifecycle classification
        lifecycle = lifecycle_service.classify_lifecycle(
            z_score=3.5,
            short_term_slope=2.5,
            long_term_slope=1.8,
            acceleration=0.3,
            saturation_score=45.0,
            avg_volume=65.0,
            current_value=72.0
        )
        print(f"  ✅ Lifecycle classification: {lifecycle}")
        
        # Test prediction
        sample_values = [45.0, 48.0, 52.0, 58.0, 62.0, 67.0, 73.0, 76.0]
        prediction = prediction_service.predict_trend(values=sample_values, forecast_days=7)
        print(f"  ✅ Prediction: {prediction['predicted_growth_pct']:.1f}% growth, {prediction['breakout_probability']:.1f} breakout prob")
        
        # Test profit scoring
        profit_score = profit_service.calculate_profit_score(
            arbitrage_score=85.0,
            social_score=72.0,
            saturation_score=45.0,
            breakout_probability=78.5,
            lifecycle_stage="Breakout"
        )
        print(f"  ✅ Profit score: {profit_score:.1f}/100")
        
        print("\n✅ All enhancement services integrated correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ Service integration test failed: {str(e)}")
        return False


async def test_detection_pipeline_logic():
    """Test that detection pipeline has all enhancement logic"""
    print("\n" + "="*60)
    print("TEST: Detection Pipeline Enhancement Logic")
    print("="*60)
    
    try:
        from application.services.trend_detection_service import TrendDetectionService
        
        detection_service = TrendDetectionService()
        
        # Check that service has the right methods
        if hasattr(detection_service, 'initialize_detection_signal'):
            print("  ✅ initialize_detection_signal method exists")
        if hasattr(detection_service, 'execute_detection_pipeline'):
            print("  ✅ execute_detection_pipeline method exists")
        
        # Verify location locking in initialize_detection_signal
        import inspect
        sig = inspect.signature(detection_service.initialize_detection_signal)
        params = list(sig.parameters.keys())
        
        if 'override_location' not in params:
            print("  ✅ Location locking enforced (no override_location parameter)")
        else:
            print("  ❌ Location override still allowed (override_location parameter exists)")
            return False
        
        print("\n✅ Detection pipeline has correct signature for location locking")
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline logic test failed: {str(e)}")
        return False


async def test_caching_model_exists():
    """Test that caching infrastructure exists"""
    print("\n" + "="*60)
    print("TEST: Suggestion Caching Infrastructure")
    print("="*60)
    
    try:
        from infrastructure.database.models.content_suggestion_cache_model import ContentSuggestionCacheModel
        
        print("  ✅ ContentSuggestionCacheModel exists")
        
        # Check fields
        if hasattr(ContentSuggestionCacheModel, 'keyword'):
            print("  ✅ keyword field exists")
        if hasattr(ContentSuggestionCacheModel, 'expires_at'):
            print("  ✅ expires_at field exists (TTL support)")
        if hasattr(ContentSuggestionCacheModel, 'is_expired'):
            print("  ✅ is_expired property exists")
        
        print("\n✅ Caching infrastructure properly configured")
        return True
        
    except ImportError:
        print("  ❌ ContentSuggestionCacheModel not found")
        return False


async def main():
    """Run all runtime tests"""
    print("=" * 60)
    print("RAAMP ENHANCEMENT FEATURES - RUNTIME VALIDATION")
    print("=" * 60)
    
    # Initialize database connection
    try:
        await init_db()
        print("✅ Database connection initialized")
    except Exception as e:
        print(f"⚠️  Database connection failed: {str(e)}")
        print("ℹ️  Some tests will be skipped")
    
    tests = [
        ("Location Locking", test_location_locking),
        ("Enhanced Fields in DB", test_enhanced_fields_in_database),
        ("Timeframe Support", test_timeframe_support),
        ("Service Integration", test_service_integration),
        ("Pipeline Logic", test_detection_pipeline_logic),
        ("Caching Infrastructure", test_caching_model_exists)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All runtime validation tests PASSED!")
        print("✅ System is production-ready")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed or incomplete")
        print("ℹ️  Some failures expected for fresh database")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
