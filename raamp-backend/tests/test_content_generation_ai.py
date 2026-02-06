"""
Direct AI Test for Content Generation
======================================
Tests the OpenAI integration directly without HTTP server.
This validates the AI response structure and quality.

Run: python tests/test_content_generation_ai.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


async def test_ai_generation():
    """Test the AI generation directly."""
    print("\n" + "=" * 70)
    print("DIRECT AI CONTENT GENERATION TEST")
    print("=" * 70 + "\n")
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set in environment")
        return False
    
    print(f"✅ API key found: {api_key[:20]}...")
    
    try:
        from application.services.content_generation_service import ContentGenerationService
        
        print("✅ Service imported successfully")
        
        service = ContentGenerationService()
        print(f"✅ Service initialized with model: {service.model}")
        
        # Test brand context
        brand_context = {
            "business_name": "Urban Bites Cafe",
            "tagline": "Fresh flavors, urban vibes",
            "tone_of_voice": "Friendly, casual, and trendy",
            "restaurant_theme": "Modern fusion street food",
            "business_type": "Restaurant",
            "primary_color": "#FF6B35",
            "secondary_color": "#2EC4B6"
        }
        
        campaign_idea = """
        Launch a weekend brunch special featuring our new avocado toast menu.
        We have 5 different variations including classic, Mediterranean, spicy Mexican,
        Asian fusion, and sweet dessert style. Prices range from $12-18.
        We want to attract young professionals and foodies who appreciate 
        Instagram-worthy food presentations. The brunch runs every Saturday and Sunday
        from 10am to 3pm with bottomless mimosas available for $15 extra.
        """
        
        print("\n" + "-" * 50)
        print("GENERATING CONTENT...")
        print("-" * 50)
        print(f"\nCampaign: {campaign_idea[:100]}...")
        print(f"Platform: Instagram")
        print(f"Target: Young professionals and foodies")
        print()
        
        start_time = datetime.now()
        
        result = await service.generate_content(
            campaign_idea=campaign_idea,
            brand_context=brand_context,
            target_audience="Young professionals aged 25-35 who love brunch and Instagram food photos",
            campaign_tone="Fun, appetizing, and FOMO-inducing",
            platform="instagram"
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"⏱️  Generation took: {duration:.2f} seconds\n")
        
        # Validate response
        print("=" * 50)
        print("RESPONSE VALIDATION")
        print("=" * 50 + "\n")
        
        tests_passed = 0
        tests_total = 0
        
        # Test 1: Success flag
        tests_total += 1
        if result.get("success"):
            print("✅ Generation successful")
            tests_passed += 1
        else:
            print(f"❌ Generation failed: {result.get('error')}")
            print(f"   Detail: {result.get('detail')}")
            return False
        
        # Test 2: Has variants
        tests_total += 1
        variants = result.get("variants", [])
        if variants:
            print(f"✅ Has variants array ({len(variants)} items)")
            tests_passed += 1
        else:
            print("❌ No variants in response")
            return False
        
        # Test 3: Exactly 3 variants
        tests_total += 1
        if len(variants) == 3:
            print("✅ Exactly 3 variants returned")
            tests_passed += 1
        else:
            print(f"❌ Expected 3 variants, got {len(variants)}")
        
        # Test 4: Variants have required fields
        required_keys = ["id", "tone", "caption", "hashtags"]
        for i, v in enumerate(variants):
            tests_total += 1
            has_all = all(k in v for k in required_keys)
            if has_all:
                print(f"✅ Variant {i+1} has all required fields")
                tests_passed += 1
            else:
                missing = [k for k in required_keys if k not in v]
                print(f"❌ Variant {i+1} missing fields: {missing}")
        
        # Test 5: Has best_variant_id
        tests_total += 1
        best_id = result.get("best_variant_id")
        if best_id in [1, 2, 3]:
            print(f"✅ Has valid best_variant_id: {best_id}")
            tests_passed += 1
        else:
            print(f"❌ Invalid best_variant_id: {best_id}")
        
        # Test 6: Has reasoning
        tests_total += 1
        reasoning = result.get("reasoning")
        if reasoning and len(reasoning) > 20:
            print(f"✅ Has reasoning ({len(reasoning)} chars)")
            tests_passed += 1
        else:
            print(f"❌ Missing or short reasoning")
        
        # Test 7: Unique tones
        tests_total += 1
        tones = [v.get("tone") for v in variants]
        if len(set(tones)) == 3:
            print(f"✅ All 3 variants have unique tones")
            tests_passed += 1
        else:
            print(f"❌ Duplicate tones found: {tones}")
        
        # Test 8: Hashtags format
        tests_total += 1
        all_valid = True
        for i, v in enumerate(variants):
            hashtags = v.get("hashtags", [])
            if not isinstance(hashtags, list) or len(hashtags) < 3:
                all_valid = False
                print(f"   ⚠️  Variant {i+1}: Only {len(hashtags)} hashtags")
            if not all(str(h).startswith("#") for h in hashtags):
                all_valid = False
                print(f"   ⚠️  Variant {i+1}: Some hashtags don't start with #")
        
        if all_valid:
            print("✅ All hashtags are properly formatted")
            tests_passed += 1
        else:
            print("❌ Some hashtag issues found")
        
        # Test 9: Caption quality
        tests_total += 1
        captions_good = all(len(v.get("caption", "")) > 50 for v in variants)
        if captions_good:
            print("✅ All captions are meaningful (>50 chars)")
            tests_passed += 1
        else:
            print("❌ Some captions are too short")
        
        # Test 10: Performance predictions
        tests_total += 1
        valid_perfs = ["Best", "Good", "Experimental"]
        perfs = [v.get("predicted_performance") for v in variants]
        if all(p in valid_perfs for p in perfs):
            print(f"✅ Valid performance predictions: {perfs}")
            tests_passed += 1
        else:
            print(f"❌ Invalid performance values: {perfs}")
        
        # Print generated content
        print("\n" + "=" * 50)
        print("GENERATED CONTENT")
        print("=" * 50)
        
        for v in variants:
            is_best = v["id"] == best_id
            badge = "⭐ AI RECOMMENDED" if is_best else ""
            
            print(f"\n{'='*40}")
            print(f"VARIANT {v['id']} - {v['tone']} {badge}")
            print(f"Performance: {v.get('predicted_performance', 'N/A')}")
            print(f"{'='*40}")
            print(f"\n📝 Caption:")
            print(f"{v['caption']}")
            print(f"\n#️⃣  Hashtags:")
            print(f"{' '.join(v['hashtags'])}")
        
        print(f"\n{'='*50}")
        print(f"💡 AI REASONING:")
        print(f"{'='*50}")
        print(f"{reasoning}")
        
        # Summary
        print(f"\n{'='*70}")
        print(f"TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Tests Passed: {tests_passed}/{tests_total}")
        print(f"Pass Rate: {tests_passed/tests_total*100:.1f}%")
        print(f"Generation Time: {duration:.2f}s")
        print(f"{'='*70}\n")
        
        return tests_passed == tests_total
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main entry point."""
    success = await test_ai_generation()
    
    if success:
        print("\n🎉 ALL AI TESTS PASSED!")
    else:
        print("\n⚠️  SOME AI TESTS FAILED")
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
