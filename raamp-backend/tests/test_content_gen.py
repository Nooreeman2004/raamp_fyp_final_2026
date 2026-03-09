import sys, os, asyncio
sys.path.insert(0, os.getcwd())
from dotenv import load_dotenv
load_dotenv()

async def run():
    from application.services.content_generation_service import ContentGenerationService
    svc = ContentGenerationService()
    brand_context = {
        "business_name": "Bloom Cafe",
        "tagline": "Where every sip inspires",
        "tone_of_voice": "warm and friendly",
        "restaurant_theme": "Botanical & minimalist",
        "business_type": "specialty coffee shop",
        "primary_color": "#2D6A4F",
        "secondary_color": "#B7E4C7",
        "brand_logo_url": None,
        "specialties": ["cold brew", "matcha latte", "avocado toast"]
    }
    for ct in ["captions", "whatsapp", "emails", "all"]:
        print(f"\n=== content_type={ct} ===")
        result = await svc.generate_content(
            campaign_idea="Summer iced coffee launch targeting young professionals who work from cafes",
            brand_context=brand_context,
            user_id="test@test.com",
            platform_type="post",
            content_type=ct
        )
        if result.get("success"):
            caps = result.get("caption_variants", [])
            msgs = result.get("message_variants", [])
            tags = result.get("hashtag_sets", [])
            print(f"  OK - captions={len(caps)}, msgs={len(msgs)}, hashtag_sets={len(tags)}")
            if msgs:
                print(f"  First msg: {str(msgs[0].get('message',''))[:100]}")
        else:
            print(f"  FAILED: {result.get('error')} - {result.get('detail','')[:120]}")

asyncio.run(run())
