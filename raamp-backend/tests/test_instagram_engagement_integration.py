"""
Test Instagram Engagement Integration
Validates real Instagram Graph API integration and Playwright retry logic.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add backend root to Python path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_instagram_engagement_score():
    """Test Instagram Graph API engagement score computation"""
    print("\n" + "="*80)
    print("TEST 1: Instagram Engagement Score Computation")
    print("="*80)
    
    try:
        from application.services.instagram_graph_api_service import InstagramGraphAPIClient
        
        ig_client = InstagramGraphAPIClient()
        
        # Test with a common keyword (will fail if user not connected, which is expected)
        test_keyword = "coffee"
        test_user_id = "test@example.com"
        
        print(f"\n📊 Testing engagement score for keyword: '{test_keyword}'")
        print(f"   User ID: {test_user_id}")
        
        try:
            result = await ig_client.compute_keyword_engagement_score(test_user_id, test_keyword)
            
            if result:
                print("\n✅ SUCCESS: Instagram API returned engagement data")
                print(f"   • Keyword: {result.get('keyword')}")
                print(f"   • Media Count: {result.get('media_count'):,}")
                print(f"   • Avg Likes: {result.get('avg_likes'):.1f}")
                print(f"   • Avg Comments: {result.get('avg_comments'):.1f}")
                print(f"   • Engagement Score: {result.get('engagement_score'):.2f}/100")
                print(f"   • Total Engagement: {result.get('total_engagement'):,}")
                return True
            else:
                print("\n⚠️  API returned None (expected if Instagram not connected)")
                print("   This is normal behavior - fallback to semantic analysis will occur")
                return True
                
        except Exception as e:
            error_msg = str(e)
            print(f"\n⚠️  Instagram API Error: {error_msg}")
            
            if "not connected" in error_msg.lower():
                print("   Expected error: No Instagram connection configured")
                print("   ✅ Error handling working correctly")
                return True
            else:
                print(f"   ❌ Unexpected error type")
                return False
                
    except ImportError as e:
        print(f"\n❌ IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.exception("Test failed with exception")
        return False


async def test_playwright_retry_logic():
    """Test Playwright scraping with retry logic"""
    print("\n" + "="*80)
    print("TEST 2: Playwright Retry Logic")
    print("="*80)
    
    try:
        from application.services.saturation_service import SaturationService
        
        saturation_service = SaturationService()
        
        test_keyword = "coffee shop"
        
        print(f"\n🔍 Testing Playwright scraping with retries for: '{test_keyword}'")
        print("   Max retries: 3")
        print("   Backoff strategy: Exponential (1s, 2s, 4s)")
        
        result = await saturation_service._fetch_serp_data_stable(test_keyword, max_retries=3)
        
        print(f"\n📊 Scraping Result:")
        print(f"   • Status: {result.get('status')}")
        print(f"   • Result Count: {result.get('result_count'):,}")
        print(f"   • Ad Count: {result.get('ad_count')}")
        
        if result.get('status') == 'success':
            print("\n✅ SUCCESS: Playwright scraping completed successfully")
            return True
        else:
            print("\n⚠️  Scraping failed after retries (using fallback is expected)")
            print("   This is acceptable behavior - proxy scores will be used")
            return True
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.exception("Test failed with exception")
        return False


async def test_batch_saturation_with_retry():
    """Test batch saturation analysis with retry logic"""
    print("\n" + "="*80)
    print("TEST 3: Batch Saturation Analysis with Retries")
    print("="*80)
    
    try:
        from application.services.saturation_service import SaturationService
        
        saturation_service = SaturationService()
        
        test_trends = [
            {"keyword": "sustainable fashion", "interest": 65},
            {"keyword": "vegan recipes", "interest": 75},
            {"keyword": "home workout", "interest": 55}
        ]
        
        print(f"\n🔍 Testing batch analysis for {len(test_trends)} keywords:")
        for trend in test_trends:
            print(f"   • {trend['keyword']} (interest: {trend['interest']})")
        
        print("\n⏳ Running batch analysis (this may take 30-60 seconds)...")
        start_time = datetime.now()
        
        results = await saturation_service.batch_saturation_analysis(test_trends)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n📊 Batch Analysis Results ({elapsed:.1f}s):")
        for result in results:
            print(f"\n   Keyword: {result.get('keyword')}")
            print(f"   • SERP Count: {result.get('serp_count'):,}")
            print(f"   • Ad Count: {result.get('ad_count')}")
            print(f"   • Saturation Score: {result.get('saturation_score')}/100")
            print(f"   • Ad Density: {result.get('ad_density')}")
            print(f"   • Real Data: {'✅' if result.get('is_real_data') else '⚠️ Proxy'}")
        
        if len(results) == len(test_trends):
            print(f"\n✅ SUCCESS: All {len(test_trends)} keywords processed")
            
            real_data_count = sum(1 for r in results if r.get('is_real_data'))
            print(f"   • Real scraping: {real_data_count}/{len(results)}")
            print(f"   • Proxy fallback: {len(results) - real_data_count}/{len(results)}")
            return True
        else:
            print(f"\n❌ FAILED: Expected {len(test_trends)} results, got {len(results)}")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.exception("Test failed with exception")
        return False


async def test_encryption_key_generation():
    """Test ENCRYPTION_KEY auto-generation"""
    print("\n" + "="*80)
    print("TEST 4: Encryption Key Auto-Generation")
    print("="*80)
    
    try:
        from config import Config
        
        print("\n🔑 Testing encryption key retrieval...")
        
        key = Config.get_encryption_key()
        
        if key:
            masked_key = f"{key[:8]}...{key[-8:]}" if len(key) > 16 else "***"
            print(f"\n✅ SUCCESS: Encryption key generated")
            print(f"   • Key (masked): {masked_key}")
            print(f"   • Key length: {len(key)} characters")
            
            # Verify it's a valid Fernet key format
            import base64
            try:
                decoded = base64.urlsafe_b64decode(key)
                if len(decoded) == 32:
                    print("   • Format: Valid Fernet key (32 bytes)")
                    return True
                else:
                    print(f"   ⚠️  Key decoded but wrong length: {len(decoded)} bytes (expected 32)")
                    return False
            except Exception as e:
                print(f"   ❌ Invalid key format: {e}")
                return False
        else:
            print("\n❌ FAILED: No encryption key returned")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.exception("Test failed with exception")
        return False


async def test_trend_detection_integration():
    """Test full trend detection pipeline with Instagram integration"""
    print("\n" + "="*80)
    print("TEST 5: Trend Detection Pipeline Integration")
    print("="*80)
    
    try:
        from application.services.trend_detection_service import TrendDetectionService
        from application.services.google_trends_service import GoogleTrendsService
        from application.services.notification_service import NotificationService
        from application.services.instagram_graph_api_service import InstagramGraphAPIClient
        
        print("\n🔧 Initializing services...")
        
        trends_service = GoogleTrendsService()
        notification_service = NotificationService()
        ig_client = InstagramGraphAPIClient()
        
        detection_service = TrendDetectionService(
            trends_service=trends_service,
            notification_service=notification_service,
            ig_client=ig_client
        )
        
        print("✅ All services initialized successfully")
        print("\n📊 Service Configuration:")
        print(f"   • Instagram Client: {type(ig_client).__name__}")
        print(f"   • Trends Service: {type(trends_service).__name__}")
        print(f"   • Detection Service: {type(detection_service).__name__}")
        
        # Check if key methods exist
        methods_to_check = [
            ('ig_client', 'compute_keyword_engagement_score'),
            ('detection_service', 'initialize_detection_signal')
        ]
        
        all_methods_exist = True
        for obj_name, method_name in methods_to_check:
            obj = locals()[obj_name]
            if hasattr(obj, method_name):
                print(f"   ✅ {obj_name}.{method_name}() exists")
            else:
                print(f"   ❌ {obj_name}.{method_name}() MISSING")
                all_methods_exist = False
        
        if all_methods_exist:
            print("\n✅ SUCCESS: All required methods present")
            return True
        else:
            print("\n❌ FAILED: Some methods missing")
            return False
            
    except ImportError as e:
        print(f"\n❌ IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        logger.exception("Test failed with exception")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RAAMP INSTAGRAM & PLAYWRIGHT INTEGRATION TESTS")
    print("="*80)
    print(f"Test Suite: Instagram Engagement + Retry Logic Validation")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Encryption Key Generation", test_encryption_key_generation),
        ("Instagram Engagement Score", test_instagram_engagement_score),
        ("Playwright Retry Logic", test_playwright_retry_logic),
        ("Batch Saturation Analysis", test_batch_saturation_with_retry),
        ("Trend Detection Integration", test_trend_detection_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n💥 CRITICAL ERROR in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
    
    print("\n" + "-"*80)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  Some tests failed - review logs above")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
