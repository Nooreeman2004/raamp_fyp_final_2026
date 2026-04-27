"""
Simple test to verify restaurant-specific content generation
Shows exactly what prompts are sent to Gemini
"""

import asyncio
import sys
import os

# Add parent directory to path to import from raamp-backend
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# Get the directory where test outputs should be saved
TEST_OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

from application.services.industry_templates import (
    build_industry_prompt_injection,
    infer_business_domain
)
from application.services.content_generation_service import ContentGenerationService


# Mock the caption logging to avoid DB initialization errors
import unittest.mock as mock

async def async_mock_return(*args, **kwargs):
    """Async mock that returns None"""
    return None

def mock_caption_repo():
    """Mock caption repository to avoid DB errors in tests"""
    mock_repo = mock.MagicMock()
    # Use AsyncMock properly for async methods
    mock_repo.log_caption_generation = mock.AsyncMock(return_value=None)
    mock_repo.log_hashtag_generation = mock.AsyncMock(return_value=None)
    mock_repo.log_message_generation = mock.AsyncMock(return_value=None)
    mock_repo.create_many = mock.AsyncMock(return_value=None)  # Fix for bulk insert
    return mock_repo


def test_industry_injection():
    """Test what build_industry_prompt_injection returns for restaurants"""
    
    print("=" * 80)
    print("TEST 1: What does build_industry_prompt_injection() return?")
    print("=" * 80)
    
    business_type = "Italian Restaurant"
    business_domain = infer_business_domain(business_type)
    
    print(f"\nBusiness Type: {business_type}")
    print(f"Inferred Domain: {business_domain}")
    print("\n" + "-" * 80)
    print("INDUSTRY INJECTION OUTPUT:")
    print("-" * 80)
    
    injection = build_industry_prompt_injection(
        business_domain=business_domain,
        business_type=business_type,
        tone_modifier=None
    )
    
    print(injection)
    print("\n")


async def test_full_prompt():
    """Test the complete prompt sent to Gemini for a restaurant"""
    
    print("=" * 80)
    print("TEST 2: Full Prompt Sent to Gemini")
    print("=" * 80)
    
    # Mock restaurant brand context
    brand_context = {
        "business_name": "Bella Italia",
        "business_type": "Italian Restaurant",
        "tagline": "Authentic Italian flavors in the heart of Karachi",
        "tone_of_voice": "Warm and inviting",
        "restaurant_theme": "Rustic Italian trattoria",
        "specialties": ["Pizza", "Pasta", "Tiramisu"],
        "city": "Karachi",
        "country": "Pakistan",
        "primary_color": "#C41E3A",
        "secondary_color": "#009246",
        "brand_colors": ["#C41E3A", "#009246", "#FFFFFF"],
        "brand_logo_url": "https://example.com/logo.png"
    }
    
    campaign_idea = "Weekend brunch special: fluffy pancakes with maple syrup and fresh berries"
    
    print("\nBrand Context:")
    for key, value in brand_context.items():
        print(f"  {key}: {value}")
    
    print(f"\nCampaign Idea: {campaign_idea}")
    print("\n" + "-" * 80)
    print("BUILDING PROMPT...")
    print("-" * 80)
    
    try:
        service = ContentGenerationService()
        
        # Build the user prompt (this is what gets combined with system prompt)
        user_prompt = service._build_user_prompt(
            campaign_idea=campaign_idea,
            brand_context=brand_context,
            target_audience=None,
            campaign_tone=None,
            platform_type="post",
            content_type="all"
        )
        
        # Get system prompt
        system_prompt = service._get_system_prompt("post")
        
        # This is what actually gets sent to Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        print("\n" + "=" * 80)
        print("SYSTEM PROMPT (First 500 chars):")
        print("=" * 80)
        print(system_prompt[:500] + "...\n")
        
        print("=" * 80)
        print("USER PROMPT (First 1000 chars):")
        print("=" * 80)
        print(user_prompt[:1000] + "...\n")
        
        print("=" * 80)
        print("FULL PROMPT LENGTH:")
        print("=" * 80)
        print(f"System Prompt: {len(system_prompt)} chars")
        print(f"User Prompt: {len(user_prompt)} chars")
        print(f"Total: {len(full_prompt)} chars")
        
        # Check for key restaurant terms
        print("\n" + "=" * 80)
        print("PROMPT ANALYSIS - Does it contain restaurant-specific language?")
        print("=" * 80)
        
        # Check user prompt only (not system prompt which contains instructions)
        checks = {
            "✓ 'dish/meal/menu item'": "dish" in user_prompt.lower() or "meal" in user_prompt.lower(),
            "✓ 'crispy/juicy/aromatic'": any(word in user_prompt.lower() for word in ["crispy", "juicy", "aromatic"]),
            "✓ 'dining experience'": "dining" in user_prompt.lower(),
            "✓ Cuisine (Pizza/Pasta)": "pizza" in user_prompt.lower() or "pasta" in user_prompt.lower(),
            "✓ Location (Karachi)": "karachi" in user_prompt.lower(),
            "✓ Restaurant-specific rules": "restaurant content rules" in user_prompt.lower()
        }
        
        for check, result in checks.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {check}")
        
        # Save full prompt to file for inspection
        prompt_file = os.path.join(TEST_OUTPUT_DIR, "test_full_prompt.txt")
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("FULL PROMPT SENT TO GEMINI\n")
            f.write("=" * 80 + "\n\n")
            f.write(full_prompt)
        
        print(f"\n✓ Full prompt saved to: {prompt_file}")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


async def test_actual_generation():
    """Test actual content generation (requires GEMINI_API_KEY)"""
    
    print("\n" + "=" * 80)
    print("TEST 3: Actual Content Generation")
    print("=" * 80)
    
    if not os.getenv("GEMINI_API_KEY"):
        print("\n⚠️  SKIPPED: GEMINI_API_KEY not set")
        print("Set GEMINI_API_KEY environment variable to test actual generation")
        return
    
    brand_context = {
        "business_name": "Bella Italia",
        "business_type": "Italian Restaurant",
        "tagline": "Authentic Italian flavors in the heart of Karachi",
        "tone_of_voice": "Warm and inviting",
        "restaurant_theme": "Rustic Italian trattoria",
        "specialties": ["Pizza", "Pasta", "Tiramisu"],
        "city": "Karachi",
        "country": "Pakistan",
        "primary_color": "#C41E3A",
        "secondary_color": "#009246",
        "brand_colors": ["#C41E3A", "#009246", "#FFFFFF"],
        "brand_logo_url": "https://example.com/logo.png"
    }
    
    campaign_idea = "Weekend brunch special: fluffy pancakes with maple syrup and fresh berries"
    
    try:
        service = ContentGenerationService()
        
        # Mock the caption repository to avoid DB errors
        service.caption_repo = mock_caption_repo()
        
        print("\n🚀 Calling Gemini API...")
        
        result = await service.generate_content(
            campaign_idea=campaign_idea,
            brand_context=brand_context,
            user_id="test@example.com",
            target_audience=None,
            campaign_tone=None,
            platform_type="post",
            content_type="captions"
        )
        
        print("\n✓ Generation successful!")
        print("\n" + "=" * 80)
        print("GENERATED CAPTIONS:")
        print("=" * 80)
        
        for i, variant in enumerate(result.get("caption_variants", []), 1):
            print(f"\nVariant {i} ({variant.get('tone', 'Unknown')}):")
            print("-" * 40)
            caption = variant.get("caption", "")
            print(caption)
            
            # Check for restaurant language
            print("\nLanguage Check:")
            
            # Expanded food-specific terms
            FOOD_TERMS = ["dish", "meal", "pizza", "pasta", "recipe", "menu",
                         "slice", "bite", "flavor", "taste", "ingredient", 
                         "mozzarella", "basil", "crust", "tomato", "cheese"]
            
            # Expanded sensory terms
            SENSORY_TERMS = ["crispy", "juicy", "aromatic", "fresh", "cheesy",
                            "creamy", "savory", "golden", "heaven", "mouthwatering",
                            "delicious", "tasty", "flavorful", "rich", "tender"]
            
            # Generic business terms (should NOT appear)
            GENERIC_TERMS = ["product", "service", "offering"]
            
            has_dish = any(word in caption.lower() for word in FOOD_TERMS)
            has_sensory = any(word in caption.lower() for word in SENSORY_TERMS)
            has_generic = any(word in caption.lower() for word in GENERIC_TERMS)
            
            print(f"  {'✓' if has_dish else '✗'} Food-specific terms: {[w for w in FOOD_TERMS if w in caption.lower()]}")
            print(f"  {'✓' if has_sensory else '✗'} Sensory language: {[w for w in SENSORY_TERMS if w in caption.lower()]}")
            print(f"  {'✓' if not has_generic else '✗'} Avoids generic terms: {[w for w in GENERIC_TERMS if w in caption.lower()] if has_generic else 'None found'}")
        
        # Save result
        import json
        result_file = os.path.join(TEST_OUTPUT_DIR, "test_generation_result.json")
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Full result saved to: {result_file}")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    
    print("\n" + "=" * 80)
    print("RESTAURANT CONTENT GENERATION TEST")
    print("=" * 80)
    print("\nThis test verifies that restaurant businesses get appropriate language")
    print("in their generated content (dish/meal vs product/service)\n")
    
    # Test 1: Industry injection
    test_industry_injection()
    
    # Test 2: Full prompt
    await test_full_prompt()
    
    # Test 3: Actual generation (if API key available)
    await test_actual_generation()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
