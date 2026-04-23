"""
Brand-Lock Content Generation Contract Tests
============================================

This suite intentionally avoids brittle checks like "prompt contains keyword X".
Instead, it validates the *contract* we care about:

- Brand lock rules are enforced via prompt constraints (business name, tagline, tone, palette, logo).
- The unified prompt schema includes captions + hashtag sets + whatsapp + email.
- Platform prompts are distinct.

These tests do NOT call external LLM APIs.
"""

import pytest

from application.services.content_generation_service import ContentGenerationService


class TestBrandLockPromptContracts:
    def test_brand_context_prompt_contains_hard_rules(self):
        service = ContentGenerationService()
        brand_context = {
            "business_name": "Acme Cafe",
            "tagline": "Brewed Bold, Served Warm",
            "tone_of_voice": "Warm, friendly, confident",
            "restaurant_theme": "Modern artisan coffee bar",
            "brand_logo_url": "/api/static/acme/logos/logo.png",
            "brand_colors": ["#00E0D0", "#09151E", "#FFFFFF"],
        }

        p = service._build_brand_context_prompt(brand_context)

        # Must be clearly marked as hard constraints
        assert "HARD RULES" in p or "HARD RULE" in p or "BRAND CONSTRAINTS" in p

        # Must require verbatim usage in text outputs
        assert 'Business name MUST appear' in p
        assert 'Tagline MUST be incorporated verbatim' in p
        assert 'Tone MUST be followed strictly' in p

        # Must include palette and logo requirements (for image prompts)
        assert "Brand Color Palette" in p or "palette" in p.lower()
        assert "#00E0D0" in p and "#09151E" in p
        assert "logo" in p.lower()

    def test_unified_user_prompt_schema_includes_all_text_types(self):
        service = ContentGenerationService()
        brand_context = {
            "business_name": "Acme Cafe",
            "tagline": "Brewed Bold, Served Warm",
            "tone_of_voice": "Warm, friendly, confident",
            "restaurant_theme": "Modern artisan coffee bar",
            "brand_logo_url": "/api/static/acme/logos/logo.png",
            "brand_colors": ["#00E0D0", "#09151E"],
        }

        user_prompt = service._build_user_prompt(
            campaign_idea="Promote a new iced latte with limited-time offer",
            target_audience="Students and young professionals",
            campaign_tone=None,
            brand_context=brand_context,
            platform_type="post",
            content_type="all",
        )

        # The schema contract: captions + hashtag_sets + whatsapp_variants + email_variants
        assert '"caption_variants"' in user_prompt
        assert '"hashtag_sets"' in user_prompt
        assert '"whatsapp_variants"' in user_prompt
        assert '"email_variants"' in user_prompt


class TestPlatformPromptContracts:
    def test_get_system_prompt_method_exists(self):
        service = ContentGenerationService()
        assert hasattr(service, "_get_system_prompt")

    def test_different_prompts_for_different_platforms(self):
        service = ContentGenerationService()
        post_prompt = service._get_system_prompt("post")
        story_prompt = service._get_system_prompt("story")
        reel_prompt = service._get_system_prompt("reel")

        assert post_prompt != story_prompt
        assert post_prompt != reel_prompt
        assert story_prompt != reel_prompt

    def test_story_prompt_mentions_story_requirements(self):
        service = ContentGenerationService()
        p = service.SYSTEM_PROMPT_STORY.lower()
        assert "story" in p
        assert "sticker" in p or "interactive" in p

    def test_reel_prompt_mentions_reel_requirements(self):
        service = ContentGenerationService()
        p = service.SYSTEM_PROMPT_REEL.lower()
        assert "reel" in p
        assert "hook" in p


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
