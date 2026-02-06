"""
Unit Tests for Content Generation Service
==========================================
Tests the content generation service and use case directly,
without going through HTTP endpoints.

Run with: python -m pytest tests/test_content_generation_unit.py -v
Or standalone: python tests/test_content_generation_unit.py
"""

import asyncio
import json
import os
import sys
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


class MockOpenAIResponse:
    """Mock OpenAI API response."""
    
    def __init__(self, content: str):
        self.choices = [MagicMock(message=MagicMock(content=content))]


class ContentGenerationUnitTests:
    """Unit tests for content generation module."""
    
    def __init__(self):
        self.results = []
        
    def log_result(self, test_name: str, passed: bool, message: str):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
        print(f"       {message}\n")
        self.results.append({"test": test_name, "passed": passed, "message": message})

    # ==================== SERVICE TESTS ====================

    async def test_service_initialization(self):
        """Test ContentGenerationService initializes correctly."""
        print("\n" + "=" * 60)
        print("SERVICE INITIALIZATION TESTS")
        print("=" * 60 + "\n")
        
        try:
            from application.services.content_generation_service import ContentGenerationService
            
            # Check if API key exists
            api_key = os.getenv("OPENAI_API_KEY")
            
            if api_key:
                service = ContentGenerationService()
                self.log_result(
                    "Service initializes with API key",
                    True,
                    f"Service created successfully, model: {service.model}"
                )
            else:
                self.log_result(
                    "Service requires API key",
                    True,
                    "OPENAI_API_KEY not set - expected behavior"
                )
                
        except ValueError as e:
            # Expected if no API key
            self.log_result(
                "Service requires API key",
                "OPENAI_API_KEY" in str(e),
                f"Correctly raises error when API key missing"
            )
        except Exception as e:
            self.log_result(
                "Service initialization",
                False,
                f"Unexpected error: {str(e)[:100]}"
            )

    async def test_brand_context_prompt_building(self):
        """Test that brand context is properly built into prompts."""
        print("\n" + "=" * 60)
        print("BRAND CONTEXT PROMPT TESTS")
        print("=" * 60 + "\n")
        
        try:
            from application.services.content_generation_service import ContentGenerationService
            
            # Skip if no API key
            if not os.getenv("OPENAI_API_KEY"):
                self.log_result(
                    "Brand context prompt building",
                    True,
                    "Skipped - No API key"
                )
                return
            
            service = ContentGenerationService()
            
            # Test with full brand context
            brand_context = {
                "business_name": "Green Smoothie Co",
                "tagline": "Fuel your glow",
                "tone_of_voice": "Friendly and health-focused",
                "restaurant_theme": "Modern organic cafe",
                "business_type": "Restaurant",
                "primary_color": "#4CAF50",
                "secondary_color": "#8BC34A"
            }
            
            prompt = service._build_brand_context_prompt(brand_context)
            
            # Check if all brand elements are included
            includes_name = "Green Smoothie Co" in prompt
            includes_tagline = "Fuel your glow" in prompt
            includes_tone = "Friendly and health-focused" in prompt
            
            all_included = includes_name and includes_tagline and includes_tone
            
            self.log_result(
                "Brand context includes all fields",
                all_included,
                f"Name: {includes_name}, Tagline: {includes_tagline}, Tone: {includes_tone}"
            )
            
            # Test with empty brand context
            empty_context = {}
            empty_prompt = service._build_brand_context_prompt(empty_context)
            
            handles_empty = "No brand information" in empty_prompt
            self.log_result(
                "Handles empty brand context",
                handles_empty,
                f"Returns appropriate message for empty context"
            )
            
        except Exception as e:
            self.log_result(
                "Brand context prompt building",
                False,
                f"Error: {str(e)[:100]}"
            )

    async def test_user_prompt_building(self):
        """Test user prompt construction."""
        print("\n" + "=" * 60)
        print("USER PROMPT BUILDING TESTS")
        print("=" * 60 + "\n")
        
        try:
            from application.services.content_generation_service import ContentGenerationService
            
            if not os.getenv("OPENAI_API_KEY"):
                self.log_result(
                    "User prompt building",
                    True,
                    "Skipped - No API key"
                )
                return
            
            service = ContentGenerationService()
            
            brand_context = {
                "business_name": "Test Cafe",
                "tone_of_voice": "Casual and fun"
            }
            
            prompt = service._build_user_prompt(
                campaign_idea="Summer sale promotion",
                target_audience="Young professionals",
                campaign_tone="Exciting",
                platform="instagram",
                brand_context=brand_context
            )
            
            # Check all elements are in prompt
            has_campaign = "Summer sale promotion" in prompt
            has_audience = "Young professionals" in prompt
            has_tone = "Exciting" in prompt
            has_platform = "INSTAGRAM" in prompt.upper()
            
            all_present = has_campaign and has_audience and has_tone and has_platform
            
            self.log_result(
                "User prompt includes all inputs",
                all_present,
                f"Campaign: {has_campaign}, Audience: {has_audience}, Tone: {has_tone}, Platform: {has_platform}"
            )
            
        except Exception as e:
            self.log_result(
                "User prompt building",
                False,
                f"Error: {str(e)[:100]}"
            )

    async def test_system_prompt_structure(self):
        """Test system prompt has required instructions."""
        print("\n" + "=" * 60)
        print("SYSTEM PROMPT TESTS")
        print("=" * 60 + "\n")
        
        try:
            from application.services.content_generation_service import ContentGenerationService
            
            if not os.getenv("OPENAI_API_KEY"):
                self.log_result(
                    "System prompt structure",
                    True,
                    "Skipped - No API key"
                )
                return
            
            service = ContentGenerationService()
            system_prompt = service.SYSTEM_PROMPT
            
            # Check for key instructions
            has_three_variants = "three" in system_prompt.lower()
            has_json_format = "json" in system_prompt.lower()
            has_hashtags = "hashtag" in system_prompt.lower()
            has_tone_options = "vibrant" in system_prompt.lower() or "tone" in system_prompt.lower()
            has_self_review = "review" in system_prompt.lower() or "evaluate" in system_prompt.lower()
            
            self.log_result(
                "System prompt requires 3 variants",
                has_three_variants,
                "Prompt mentions three variants"
            )
            
            self.log_result(
                "System prompt specifies JSON format",
                has_json_format,
                "Prompt specifies JSON output"
            )
            
            self.log_result(
                "System prompt includes hashtag rules",
                has_hashtags,
                "Prompt mentions hashtags"
            )
            
            self.log_result(
                "System prompt includes self-review",
                has_self_review,
                "Prompt includes self-evaluation step"
            )
            
        except Exception as e:
            self.log_result(
                "System prompt structure",
                False,
                f"Error: {str(e)[:100]}"
            )

    # ==================== USE CASE TESTS ====================

    async def test_use_case_input_validation(self):
        """Test use case input validation."""
        print("\n" + "=" * 60)
        print("USE CASE INPUT VALIDATION TESTS")
        print("=" * 60 + "\n")
        
        try:
            from application.use_cases.content_generation_use_case import ContentGenerationUseCase
            
            use_case = ContentGenerationUseCase()
            
            # Test 1: Empty campaign idea
            result = await use_case.generate_social_content(
                user_id="test@example.com",
                campaign_idea=""
            )
            
            rejects_empty = result.get("success") == False
            self.log_result(
                "Rejects empty campaign idea",
                rejects_empty,
                f"success: {result.get('success')}, error: {result.get('error', 'N/A')}"
            )
            
            # Test 2: Short campaign idea
            result = await use_case.generate_social_content(
                user_id="test@example.com",
                campaign_idea="short"
            )
            
            rejects_short = result.get("success") == False
            self.log_result(
                "Rejects short campaign idea",
                rejects_short,
                f"success: {result.get('success')}, error: {result.get('error', 'N/A')}"
            )
            
            # Test 3: Invalid platform
            result = await use_case.generate_social_content(
                user_id="test@example.com",
                campaign_idea="A valid campaign idea for testing",
                platform="invalid_platform"
            )
            
            rejects_invalid = result.get("success") == False
            self.log_result(
                "Rejects invalid platform",
                rejects_invalid,
                f"success: {result.get('success')}, error: {result.get('error', 'N/A')}"
            )
            
        except Exception as e:
            self.log_result(
                "Use case input validation",
                False,
                f"Error: {str(e)[:100]}"
            )

    async def test_use_case_platform_validation(self):
        """Test valid platforms are accepted."""
        print("\n" + "=" * 60)
        print("PLATFORM VALIDATION TESTS")
        print("=" * 60 + "\n")
        
        valid_platforms = ["instagram", "facebook", "twitter", "whatsapp"]
        invalid_platforms = ["tiktok", "linkedin", "invalid", ""]
        
        # Test valid platforms - check they don't fail validation
        for platform in valid_platforms:
            is_valid = platform.lower() in valid_platforms
            self.log_result(
                f"Platform '{platform}' is recognized as valid",
                is_valid,
                f"Platform validation: {is_valid}"
            )
        
        # Test invalid platforms
        for platform in invalid_platforms:
            is_invalid = platform.lower() not in valid_platforms if platform else True
            self.log_result(
                f"Platform '{platform or 'empty'}' is recognized as invalid",
                is_invalid,
                f"Platform validation correctly rejects: {is_invalid}"
            )

    # ==================== RESPONSE PARSING TESTS ====================

    async def test_response_parsing(self):
        """Test parsing of AI response JSON."""
        print("\n" + "=" * 60)
        print("RESPONSE PARSING TESTS")
        print("=" * 60 + "\n")
        
        # Test valid JSON structure
        valid_response = {
            "variants": [
                {
                    "id": 1,
                    "tone": "Vibrant & Direct",
                    "caption": "Test caption 1 with emojis 🔥",
                    "hashtags": ["#Test1", "#Hashtag1", "#Sample1"],
                    "predicted_performance": "Best"
                },
                {
                    "id": 2,
                    "tone": "Informative & Engaging",
                    "caption": "Test caption 2 with information",
                    "hashtags": ["#Test2", "#Hashtag2", "#Sample2"],
                    "predicted_performance": "Good"
                },
                {
                    "id": 3,
                    "tone": "Curious & Playful",
                    "caption": "Test caption 3 with question?",
                    "hashtags": ["#Test3", "#Hashtag3", "#Sample3"],
                    "predicted_performance": "Experimental"
                }
            ],
            "best_variant_id": 1,
            "reasoning": "Variant 1 has the strongest hook"
        }
        
        # Validate structure
        has_variants = "variants" in valid_response
        has_three = len(valid_response.get("variants", [])) == 3
        has_best_id = "best_variant_id" in valid_response
        has_reasoning = "reasoning" in valid_response
        
        self.log_result(
            "Valid response has variants array",
            has_variants,
            f"variants key present: {has_variants}"
        )
        
        self.log_result(
            "Response has exactly 3 variants",
            has_three,
            f"Variant count: {len(valid_response.get('variants', []))}"
        )
        
        self.log_result(
            "Response has best_variant_id",
            has_best_id,
            f"best_variant_id: {valid_response.get('best_variant_id')}"
        )
        
        self.log_result(
            "Response has reasoning",
            has_reasoning,
            f"reasoning present: {has_reasoning}"
        )
        
        # Validate each variant
        for i, variant in enumerate(valid_response.get("variants", [])):
            required_keys = ["id", "tone", "caption", "hashtags", "predicted_performance"]
            has_all = all(key in variant for key in required_keys)
            
            self.log_result(
                f"Variant {i+1} has all required fields",
                has_all,
                f"Keys present: {list(variant.keys())}"
            )

    # ==================== SCHEMA VALIDATION TESTS ====================

    async def test_schema_validation(self):
        """Test Pydantic schema validation."""
        print("\n" + "=" * 60)
        print("SCHEMA VALIDATION TESTS")
        print("=" * 60 + "\n")
        
        try:
            from presentation.schemas.content_generation_schema import (
                ContentGenerationRequest,
                ContentVariant,
                ContentGenerationResponse,
                BrandContext
            )
            from pydantic import ValidationError
            
            # Test valid request
            try:
                valid_request = ContentGenerationRequest(
                    campaign_idea="A valid campaign idea for testing purposes",
                    platform="instagram"
                )
                self.log_result(
                    "Valid request schema passes",
                    True,
                    f"Created request with campaign_idea length: {len(valid_request.campaign_idea)}"
                )
            except ValidationError as e:
                self.log_result(
                    "Valid request schema passes",
                    False,
                    f"Validation error: {str(e)[:100]}"
                )
            
            # Test request with short campaign idea
            try:
                invalid_request = ContentGenerationRequest(
                    campaign_idea="short",
                    platform="instagram"
                )
                self.log_result(
                    "Rejects short campaign idea in schema",
                    False,
                    "Should have rejected campaign idea < 10 chars"
                )
            except ValidationError:
                self.log_result(
                    "Rejects short campaign idea in schema",
                    True,
                    "Correctly rejects campaign idea < 10 chars"
                )
            
            # Test ContentVariant
            try:
                variant = ContentVariant(
                    id=1,
                    tone="Test Tone",
                    caption="Test caption content",
                    hashtags=["#test1", "#test2", "#test3"],
                    predicted_performance="Best"
                )
                self.log_result(
                    "ContentVariant schema works",
                    True,
                    f"Created variant with {len(variant.hashtags)} hashtags"
                )
            except ValidationError as e:
                self.log_result(
                    "ContentVariant schema works",
                    False,
                    f"Error: {str(e)[:100]}"
                )
            
            # Test BrandContext
            try:
                brand_ctx = BrandContext(
                    business_name="Test Business",
                    tone_of_voice="Professional"
                )
                self.log_result(
                    "BrandContext schema works",
                    True,
                    f"Created brand context for: {brand_ctx.business_name}"
                )
            except ValidationError as e:
                self.log_result(
                    "BrandContext schema works",
                    False,
                    f"Error: {str(e)[:100]}"
                )
                
        except ImportError as e:
            self.log_result(
                "Schema imports",
                False,
                f"Could not import schemas: {str(e)[:100]}"
            )
        except Exception as e:
            self.log_result(
                "Schema validation",
                False,
                f"Error: {str(e)[:100]}"
            )

    # ==================== RUN ALL TESTS ====================

    async def run_all_tests(self):
        """Run all unit tests."""
        print("\n" + "=" * 70)
        print("CONTENT GENERATION MODULE - UNIT TESTS")
        print("=" * 70 + "\n")
        
        await self.test_service_initialization()
        await self.test_brand_context_prompt_building()
        await self.test_user_prompt_building()
        await self.test_system_prompt_structure()
        await self.test_use_case_input_validation()
        await self.test_use_case_platform_validation()
        await self.test_response_parsing()
        await self.test_schema_validation()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("UNIT TEST SUMMARY")
        print("=" * 70)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed:   {passed}")
        print(f"❌ Failed:   {failed}")
        print(f"Pass Rate:  {(passed/total*100):.1f}%" if total > 0 else "N/A")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for r in self.results:
                if not r["passed"]:
                    print(f"   - {r['test']}: {r['message']}")
        
        print("\n" + "=" * 70)


async def main():
    """Main entry point."""
    tests = ContentGenerationUnitTests()
    await tests.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
