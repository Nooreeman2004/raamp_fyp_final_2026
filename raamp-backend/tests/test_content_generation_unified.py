"""
Test Content Generation with Unified Gemini SDK
==============================================
Direct test of the content generation service to diagnose issues.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from application.services.content_generation_service import get_content_generation_service


async def test_content_generation():
    """Test content generation with a simple campaign idea."""
    print("\n" + "=" * 80)
    print("TESTING CONTENT GENERATION SERVICE")
    print("=" * 80)
    
    # Check environment variables
    print("\n📋 Environment Check:")
    gemini_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash")
    
    print(f"   GEMINI_API_KEY: {'✓ Set' if gemini_key else '✗ Missing'}")
    if gemini_key:
        print(f"   Key length: {len(gemini_key)} chars")
        print(f"   Key starts with: {gemini_key[:20]}...")
    print(f"   GEMINI_TEXT_MODEL: {gemini_model}")
    
    # Test data
    campaign_idea = "Launch a new artisan coffee blend with sustainable sourcing"
    brand_context = {
        "business_name": "Artisan Coffee Co",
        "business_type": "Coffee Shop",
        "tone_of_voice": "Warm and friendly",
        "primary_color": "#8B4513",
        "tagline": "Brewing Excellence, One Cup at a Time"
    }
    user_id = "test@example.com"
    
    print("\n📝 Test Parameters:")
    print(f"   Campaign: {campaign_idea}")
    print(f"   Business: {brand_context['business_name']}")
    print(f"   User ID: {user_id}")
    
    # Initialize service
    print("\n🔧 Initializing service...")
    try:
        service = get_content_generation_service()
        print("   ✓ Service initialized successfully")
    except Exception as e:
        print(f"   ✗ Service initialization failed: {e}")
        return
    
    # Generate content
    print("\n🚀 Generating content...")
    print("   This may take 10-15 seconds...")
    
    try:
        result = await service.generate_content(
            campaign_idea=campaign_idea,
            brand_context=brand_context,
            user_id=user_id,
            target_audience="Coffee enthusiasts aged 25-45",
            campaign_tone="Enthusiastic and eco-conscious"
        )
        
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        
        if result.get("success"):
            print("\n✅ SUCCESS!")
            print(f"\n📊 Generated Content:")
            print(f"   • Caption variants: {len(result.get('caption_variants', []))}")
            print(f"   • Hashtag sets: {len(result.get('hashtag_sets', []))}")
            print(f"   • Message variants: {len(result.get('message_variants', []))}")
            print(f"   • Image prompts: {len(result.get('image_prompts', []))}")
            
            # Show first caption
            captions = result.get("caption_variants", [])
            if captions:
                print(f"\n📝 First Caption ({captions[0].get('tone')}):")
                print(f"   {captions[0].get('caption')}")
                print(f"   Hashtags: {', '.join(captions[0].get('hashtags', [])[:3])}...")
            
            # Show first message
            messages = result.get("message_variants", [])
            if messages:
                print(f"\n💬 First Message ({messages[0].get('tone')}):")
                msg_lines = messages[0].get('message', '').split('\n')
                for line in msg_lines[:3]:
                    print(f"   {line}")
                if len(msg_lines) > 3:
                    print("   ...")
            
            print("\n✨ Test completed successfully!")
            
        else:
            print("\n❌ GENERATION FAILED")
            print(f"   Error: {result.get('error')}")
            print(f"   Detail: {result.get('detail')}")
        
    except Exception as e:
        print(f"\n❌ EXCEPTION DURING GENERATION")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        print(f"\n   Traceback:")
        traceback.print_exc()
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_content_generation())
