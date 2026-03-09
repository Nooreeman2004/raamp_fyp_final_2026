"""
Test Script for Gemini Content Generation
==========================================
Tests the content generation service with the unified Gemini SDK.
"""

import os
import sys
import io
import asyncio
import json
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Test 1: Check environment variables
print("=" * 80)
print("TEST 1: Environment Variables")
print("=" * 80)

gemini_key = os.getenv("GEMINI_API_KEY")
text_model = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash")

print(f"GEMINI_API_KEY: {gemini_key[:15]}..." if gemini_key else "❌ NOT SET")
print(f"GEMINI_TEXT_MODEL: {text_model}")
print()

if not gemini_key:
    print("❌ GEMINI_API_KEY is not set. Please check your .env file.")
    sys.exit(1)

# Test 2: Import and initialize service
print("=" * 80)
print("TEST 2: Import and Initialize Content Generation Service")
print("=" * 80)

try:
    from application.services.content_generation_service import ContentGenerationService
    print("✅ Successfully imported ContentGenerationService")
    
    service = ContentGenerationService()
    print("✅ Successfully initialized ContentGenerationService")
    print(f"   Model: {service.model}")
    print(f"   API Key: {service.api_key[:15]}...")
except Exception as e:
    print(f"❌ Failed to initialize service: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Test Gemini API directly
print("=" * 80)
print("TEST 3: Direct Gemini API Test")
print("=" * 80)

try:
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=gemini_key)
    print("✅ Created Gemini client")
    
    test_prompt = """Generate a simple JSON response with this format:
{
    "test": "success",
    "message": "Gemini API is working"
}"""
    
    print(f"📤 Sending test request to {text_model}...")
    
    response = client.models.generate_content(
        model=text_model,
        contents=test_prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=100,
            response_mime_type="application/json"
        )
    )
    
    print("✅ Received response from Gemini")
    print(f"📥 Response: {response.text}")
    
    # Try to parse as JSON
    parsed = json.loads(response.text)
    print(f"✅ Successfully parsed JSON: {parsed}")
    
except Exception as e:
    print(f"❌ Direct API test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Test content generation with async
print("=" * 80)
print("TEST 4: Content Generation Service Test (Async)")
print("=" * 80)

async def test_content_generation():
    try:
        print("🚀 Starting content generation test...")
        
        # Prepare test data
        campaign_idea = "Summer sale for our new ice cream flavors - 20% off all weekend"
        brand_context = {
            "business_name": "Sweet Dreams Ice Cream",
            "business_type": "Restaurant/Cafe",
            "tone_of_voice": "Friendly and playful",
            "primary_color": "#FF6B9D",
            "secondary_color": "#C44569"
        }
        
        print(f"📝 Campaign: {campaign_idea}")
        print(f"🏢 Brand: {brand_context['business_name']}")
        
        # Call the service
        result = await service.generate_content(
            campaign_idea=campaign_idea,
            brand_context=brand_context,
            user_id="test@example.com",
            target_audience="Young adults and families",
            campaign_tone="Exciting and energetic"
        )
        
        print("\n📊 Result:")
        if result.get("success"):
            print("✅ Content generation SUCCESSFUL!")
            print(f"\n📝 Caption Variants: {len(result.get('caption_variants', []))}")
            print(f"📱 Message Variants: {len(result.get('message_variants', []))}")
            print(f"#️⃣ Hashtag Sets: {len(result.get('hashtag_sets', []))}")
            print(f"🖼️ Image Prompts: {len(result.get('image_prompts', []))}")
            
            # Show first caption
            if result.get('caption_variants'):
                first_caption = result['caption_variants'][0]
                print(f"\n📝 First Caption ({first_caption.get('tone')}):")
                print(f"   {first_caption.get('caption')}")
                print(f"   {' '.join(first_caption.get('hashtags', [])[:5])}")
        else:
            print(f"❌ Content generation FAILED!")
            print(f"Error: {result.get('error')}")
            print(f"Detail: {result.get('detail')}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

# Run the async test
print("Running async content generation test...")
asyncio.run(test_content_generation())

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
