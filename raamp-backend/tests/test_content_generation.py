"""
Test Content Generation Module
==============================
Comprehensive tests for the AI-powered social media content generation feature.
Tests include:
- Endpoint availability and authentication
- API request/response validation
- AI response structure verification
- Brand context integration
- Platform-specific content validation
- Error handling
"""

import httpx
import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@example.com")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "testpassword123")


class ContentGenerationTestSuite:
    """Comprehensive test suite for content generation module."""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.auth_token: Optional[str] = None
        self.results: List[Dict[str, Any]] = []
        
    def log_result(self, test_name: str, passed: bool, message: str, details: Any = None):
        """Log a test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "details": details
        }
        self.results.append(result)
        print(f"{status} | {test_name}")
        print(f"       {message}")
        if details and not passed:
            print(f"       Details: {json.dumps(details, indent=2)[:500]}")
        print()
        
    async def authenticate(self, client: httpx.AsyncClient) -> bool:
        """Get authentication token for protected endpoints."""
        try:
            response = await client.post(
                f"{self.base_url}/api/auth/signin",
                json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                return True
            return False
        except Exception as e:
            print(f"⚠️  Authentication failed: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    # ==================== ENDPOINT TESTS ====================
    
    async def test_endpoints_exist(self, client: httpx.AsyncClient):
        """Test that all content generation endpoints are registered."""
        print("\n" + "=" * 60)
        print("ENDPOINT AVAILABILITY TESTS")
        print("=" * 60 + "\n")
        
        endpoints = [
            ("POST", "/api/content/generate", "Content generation endpoint"),
            ("GET", "/api/content/brand-context", "Brand context endpoint"),
            ("GET", "/api/content/platforms", "Platforms list endpoint"),
        ]
        
        for method, path, description in endpoints:
            try:
                url = f"{self.base_url}{path}"
                if method == "GET":
                    response = await client.get(url, headers=self.get_headers(), timeout=5.0)
                else:
                    response = await client.post(url, json={}, headers=self.get_headers(), timeout=5.0)
                
                # Endpoint exists if we get anything other than 404
                endpoint_exists = response.status_code != 404
                
                self.log_result(
                    f"Endpoint {method} {path}",
                    endpoint_exists,
                    f"{description} - Status: {response.status_code}",
                    {"status_code": response.status_code} if not endpoint_exists else None
                )
            except httpx.ConnectError:
                self.log_result(
                    f"Endpoint {method} {path}",
                    False,
                    "Backend server not running",
                    None
                )
                return  # Stop if server not running
            except Exception as e:
                self.log_result(
                    f"Endpoint {method} {path}",
                    False,
                    f"Error: {str(e)[:100]}",
                    None
                )

    async def test_authentication_required(self, client: httpx.AsyncClient):
        """Test that endpoints require authentication."""
        print("\n" + "=" * 60)
        print("AUTHENTICATION TESTS")
        print("=" * 60 + "\n")
        
        # Test without auth token
        endpoints = [
            ("POST", "/api/content/generate"),
            ("GET", "/api/content/brand-context"),
        ]
        
        for method, path in endpoints:
            try:
                url = f"{self.base_url}{path}"
                # No auth headers
                if method == "GET":
                    response = await client.get(url, timeout=5.0)
                else:
                    response = await client.post(url, json={"campaign_idea": "test"}, timeout=5.0)
                
                requires_auth = response.status_code in [401, 403]
                
                self.log_result(
                    f"Auth required for {method} {path}",
                    requires_auth,
                    f"Returns {response.status_code} without auth (expected 401/403)",
                    {"actual_status": response.status_code} if not requires_auth else None
                )
            except Exception as e:
                self.log_result(
                    f"Auth required for {method} {path}",
                    False,
                    f"Error: {str(e)[:100]}",
                    None
                )

    # ==================== PLATFORMS ENDPOINT TESTS ====================
    
    async def test_platforms_endpoint(self, client: httpx.AsyncClient):
        """Test the platforms endpoint returns correct data."""
        print("\n" + "=" * 60)
        print("PLATFORMS ENDPOINT TESTS")
        print("=" * 60 + "\n")
        
        try:
            response = await client.get(
                f"{self.base_url}/api/content/platforms",
                timeout=5.0
            )
            
            # Test response status
            self.log_result(
                "Platforms endpoint status",
                response.status_code == 200,
                f"Expected 200, got {response.status_code}",
                None
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Test response structure
                has_platforms_key = "platforms" in data
                self.log_result(
                    "Platforms response structure",
                    has_platforms_key,
                    f"Response has 'platforms' key: {has_platforms_key}",
                    data if not has_platforms_key else None
                )
                
                if has_platforms_key:
                    platforms = data["platforms"]
                    
                    # Test platform count
                    expected_platforms = ["instagram", "facebook", "twitter", "whatsapp"]
                    platform_ids = [p.get("id") for p in platforms]
                    
                    all_platforms_present = all(p in platform_ids for p in expected_platforms)
                    self.log_result(
                        "All platforms present",
                        all_platforms_present,
                        f"Expected: {expected_platforms}, Got: {platform_ids}",
                        None
                    )
                    
                    # Test platform structure
                    if platforms:
                        first_platform = platforms[0]
                        required_keys = ["id", "name", "description", "guidelines"]
                        has_all_keys = all(key in first_platform for key in required_keys)
                        
                        self.log_result(
                            "Platform object structure",
                            has_all_keys,
                            f"Required keys: {required_keys}",
                            first_platform if not has_all_keys else None
                        )
                        
        except Exception as e:
            self.log_result(
                "Platforms endpoint",
                False,
                f"Error: {str(e)[:100]}",
                None
            )

    # ==================== BRAND CONTEXT TESTS ====================
    
    async def test_brand_context_endpoint(self, client: httpx.AsyncClient):
        """Test the brand context endpoint."""
        print("\n" + "=" * 60)
        print("BRAND CONTEXT ENDPOINT TESTS")
        print("=" * 60 + "\n")
        
        if not self.auth_token:
            self.log_result(
                "Brand context endpoint",
                False,
                "Skipped - No authentication token",
                None
            )
            return
        
        try:
            response = await client.get(
                f"{self.base_url}/api/content/brand-context",
                headers=self.get_headers(),
                timeout=10.0
            )
            
            self.log_result(
                "Brand context endpoint status",
                response.status_code == 200,
                f"Expected 200, got {response.status_code}",
                None
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Test response structure
                expected_keys = [
                    "business_name", "tagline", "tone_of_voice",
                    "restaurant_theme", "business_type", "primary_color", "secondary_color"
                ]
                
                has_expected_structure = all(key in data for key in expected_keys)
                self.log_result(
                    "Brand context response structure",
                    has_expected_structure,
                    f"Has all expected keys: {expected_keys}",
                    {"missing_keys": [k for k in expected_keys if k not in data]} if not has_expected_structure else None
                )
                
        except Exception as e:
            self.log_result(
                "Brand context endpoint",
                False,
                f"Error: {str(e)[:100]}",
                None
            )

    # ==================== CONTENT GENERATION TESTS ====================
    
    async def test_content_generation_validation(self, client: httpx.AsyncClient):
        """Test input validation for content generation."""
        print("\n" + "=" * 60)
        print("CONTENT GENERATION VALIDATION TESTS")
        print("=" * 60 + "\n")
        
        if not self.auth_token:
            self.log_result(
                "Content generation validation",
                False,
                "Skipped - No authentication token",
                None
            )
            return
        
        # Test 1: Empty campaign idea
        try:
            response = await client.post(
                f"{self.base_url}/api/content/generate",
                headers=self.get_headers(),
                json={"campaign_idea": "", "platform": "instagram"},
                timeout=10.0
            )
            
            rejects_empty = response.status_code in [400, 422]
            self.log_result(
                "Rejects empty campaign idea",
                rejects_empty,
                f"Expected 400/422, got {response.status_code}",
                None
            )
        except Exception as e:
            self.log_result(
                "Rejects empty campaign idea",
                False,
                f"Error: {str(e)[:100]}",
                None
            )
        
        # Test 2: Campaign idea too short
        try:
            response = await client.post(
                f"{self.base_url}/api/content/generate",
                headers=self.get_headers(),
                json={"campaign_idea": "short", "platform": "instagram"},
                timeout=10.0
            )
            
            rejects_short = response.status_code in [400, 422]
            self.log_result(
                "Rejects short campaign idea (<10 chars)",
                rejects_short,
                f"Expected 400/422, got {response.status_code}",
                None
            )
        except Exception as e:
            self.log_result(
                "Rejects short campaign idea",
                False,
                f"Error: {str(e)[:100]}",
                None
            )
        
        # Test 3: Invalid platform
        try:
            response = await client.post(
                f"{self.base_url}/api/content/generate",
                headers=self.get_headers(),
                json={"campaign_idea": "A valid campaign idea for testing purposes", "platform": "tiktok"},
                timeout=10.0
            )
            
            # Should either reject or use default platform
            self.log_result(
                "Handles invalid platform",
                response.status_code in [200, 400, 422],
                f"Response status: {response.status_code}",
                None
            )
        except Exception as e:
            self.log_result(
                "Handles invalid platform",
                False,
                f"Error: {str(e)[:100]}",
                None
            )

    async def test_content_generation_success(self, client: httpx.AsyncClient):
        """Test successful content generation and validate AI response."""
        print("\n" + "=" * 60)
        print("CONTENT GENERATION SUCCESS TESTS")
        print("=" * 60 + "\n")
        
        if not self.auth_token:
            self.log_result(
                "Content generation success",
                False,
                "Skipped - No authentication token",
                None
            )
            return
        
        # Test with a good campaign idea
        campaign_idea = """
        Create a summer promotion campaign for our new organic smoothie line.
        Target health-conscious millennials and Gen Z in urban areas.
        Emphasize fresh ingredients, sustainability, and the refreshing taste.
        """
        
        try:
            response = await client.post(
                f"{self.base_url}/api/content/generate",
                headers=self.get_headers(),
                json={
                    "campaign_idea": campaign_idea,
                    "target_audience": "Health-conscious millennials aged 25-35",
                    "campaign_tone": "Energetic and playful",
                    "platform": "instagram"
                },
                timeout=60.0  # Longer timeout for AI generation
            )
            
            # Test 1: Response status
            self.log_result(
                "Generation returns 200",
                response.status_code == 200,
                f"Expected 200, got {response.status_code}",
                response.text[:500] if response.status_code != 200 else None
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Test 2: Success flag
                self.log_result(
                    "Response has success=true",
                    data.get("success") == True,
                    f"success: {data.get('success')}",
                    None
                )
                
                # Test 3: Has variants array
                has_variants = "variants" in data and isinstance(data["variants"], list)
                self.log_result(
                    "Response has variants array",
                    has_variants,
                    f"variants present: {has_variants}",
                    None
                )
                
                if has_variants:
                    variants = data["variants"]
                    
                    # Test 4: Exactly 3 variants
                    has_three = len(variants) == 3
                    self.log_result(
                        "Returns exactly 3 variants",
                        has_three,
                        f"Expected 3, got {len(variants)}",
                        None
                    )
                    
                    # Test 5: Each variant has required fields
                    required_variant_keys = ["id", "tone", "caption", "hashtags"]
                    for i, variant in enumerate(variants):
                        has_all_keys = all(key in variant for key in required_variant_keys)
                        self.log_result(
                            f"Variant {i+1} has required fields",
                            has_all_keys,
                            f"Required: {required_variant_keys}",
                            {"missing": [k for k in required_variant_keys if k not in variant]} if not has_all_keys else None
                        )
                    
                    # Test 6: Variants have different tones
                    tones = [v.get("tone") for v in variants]
                    unique_tones = len(set(tones)) == len(tones)
                    self.log_result(
                        "Variants have unique tones",
                        unique_tones,
                        f"Tones: {tones}",
                        None
                    )
                    
                    # Test 7: Captions are not empty
                    captions_valid = all(len(v.get("caption", "")) > 20 for v in variants)
                    self.log_result(
                        "Captions are meaningful (>20 chars)",
                        captions_valid,
                        f"Caption lengths: {[len(v.get('caption', '')) for v in variants]}",
                        None
                    )
                    
                    # Test 8: Hashtags are arrays with hashtag format
                    for i, variant in enumerate(variants):
                        hashtags = variant.get("hashtags", [])
                        is_array = isinstance(hashtags, list)
                        has_hashtags = len(hashtags) >= 3
                        all_start_with_hash = all(str(h).startswith("#") for h in hashtags) if hashtags else False
                        
                        self.log_result(
                            f"Variant {i+1} has valid hashtags",
                            is_array and has_hashtags and all_start_with_hash,
                            f"Count: {len(hashtags)}, Format valid: {all_start_with_hash}",
                            hashtags[:5] if not (has_hashtags and all_start_with_hash) else None
                        )
                    
                    # Test 9: Has predicted performance
                    has_performance = all("predicted_performance" in v for v in variants)
                    valid_performances = ["Best", "Good", "Experimental"]
                    performances_valid = all(v.get("predicted_performance") in valid_performances for v in variants)
                    
                    self.log_result(
                        "Variants have valid performance predictions",
                        has_performance and performances_valid,
                        f"Performances: {[v.get('predicted_performance') for v in variants]}",
                        None
                    )
                
                # Test 10: Has best_variant_id
                has_best = "best_variant_id" in data
                best_valid = data.get("best_variant_id") in [1, 2, 3] if has_best else False
                self.log_result(
                    "Response has valid best_variant_id",
                    has_best and best_valid,
                    f"best_variant_id: {data.get('best_variant_id')}",
                    None
                )
                
                # Test 11: Has reasoning
                has_reasoning = "reasoning" in data and data.get("reasoning")
                self.log_result(
                    "Response has AI reasoning",
                    has_reasoning,
                    f"Reasoning present: {has_reasoning}",
                    {"reasoning": data.get("reasoning", "")[:200]} if has_reasoning else None
                )
                
                # Test 12: Has generated_at timestamp
                has_timestamp = "generated_at" in data
                self.log_result(
                    "Response has generated_at timestamp",
                    has_timestamp,
                    f"generated_at: {data.get('generated_at')}",
                    None
                )
                
                # Test 13: Has platform in response
                correct_platform = data.get("platform") == "instagram"
                self.log_result(
                    "Response platform matches request",
                    correct_platform,
                    f"Expected: instagram, Got: {data.get('platform')}",
                    None
                )
                
                # Test 14: Has brand_context in response
                has_brand_context = "brand_context" in data
                self.log_result(
                    "Response includes brand_context",
                    has_brand_context,
                    f"brand_context present: {has_brand_context}",
                    None
                )
                
        except httpx.ReadTimeout:
            self.log_result(
                "Content generation",
                False,
                "Request timed out (>60s) - AI generation too slow or failed",
                None
            )
        except Exception as e:
            self.log_result(
                "Content generation",
                False,
                f"Error: {str(e)[:200]}",
                None
            )

    async def test_platform_specific_content(self, client: httpx.AsyncClient):
        """Test that content is optimized for different platforms."""
        print("\n" + "=" * 60)
        print("PLATFORM-SPECIFIC CONTENT TESTS")
        print("=" * 60 + "\n")
        
        if not self.auth_token:
            self.log_result(
                "Platform-specific tests",
                False,
                "Skipped - No authentication token",
                None
            )
            return
        
        campaign_idea = "Promote our weekend brunch special with 20% off for families."
        
        platforms_to_test = [
            ("instagram", {"max_caption": 2200, "hashtags_expected": True}),
            ("twitter", {"max_caption": 280, "hashtags_expected": True}),
            ("whatsapp", {"max_caption": 1000, "hashtags_expected": False}),
        ]
        
        for platform, specs in platforms_to_test:
            try:
                response = await client.post(
                    f"{self.base_url}/api/content/generate",
                    headers=self.get_headers(),
                    json={
                        "campaign_idea": campaign_idea,
                        "platform": platform
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    variants = data.get("variants", [])
                    
                    # Check caption length for Twitter
                    if platform == "twitter":
                        caption_lengths = [len(v.get("caption", "")) for v in variants]
                        all_fit_twitter = all(l <= 280 for l in caption_lengths)
                        self.log_result(
                            f"{platform.upper()}: Captions fit platform limit",
                            all_fit_twitter,
                            f"Lengths: {caption_lengths} (max 280)",
                            None
                        )
                    else:
                        self.log_result(
                            f"{platform.upper()}: Content generated",
                            len(variants) == 3,
                            f"Generated {len(variants)} variants",
                            None
                        )
                else:
                    self.log_result(
                        f"{platform.upper()}: Content generation",
                        False,
                        f"Failed with status {response.status_code}",
                        None
                    )
                    
            except Exception as e:
                self.log_result(
                    f"{platform.upper()}: Content generation",
                    False,
                    f"Error: {str(e)[:100]}",
                    None
                )

    # ==================== AI RESPONSE QUALITY TESTS ====================
    
    async def test_ai_response_quality(self, client: httpx.AsyncClient):
        """Test AI response quality and relevance."""
        print("\n" + "=" * 60)
        print("AI RESPONSE QUALITY TESTS")
        print("=" * 60 + "\n")
        
        if not self.auth_token:
            self.log_result(
                "AI response quality tests",
                False,
                "Skipped - No authentication token",
                None
            )
            return
        
        # Test with specific keywords that should appear in response
        campaign_idea = """
        Launch a Valentine's Day special dinner for couples.
        Include romantic candlelit ambiance, special 4-course meal,
        complimentary champagne, and live music.
        Price: $99 per couple.
        """
        
        try:
            response = await client.post(
                f"{self.base_url}/api/content/generate",
                headers=self.get_headers(),
                json={
                    "campaign_idea": campaign_idea,
                    "target_audience": "Couples aged 25-45 celebrating Valentine's Day",
                    "platform": "instagram"
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                variants = data.get("variants", [])
                
                # Check if AI captured key themes
                all_captions = " ".join([v.get("caption", "").lower() for v in variants])
                all_hashtags = " ".join([" ".join(v.get("hashtags", [])).lower() for v in variants])
                combined_text = all_captions + " " + all_hashtags
                
                # Keywords that should appear in at least one variant
                relevant_keywords = ["valentine", "romantic", "love", "couple", "dinner", "special"]
                keywords_found = [kw for kw in relevant_keywords if kw in combined_text]
                
                relevance_score = len(keywords_found) / len(relevant_keywords)
                
                self.log_result(
                    "AI captures campaign themes",
                    relevance_score >= 0.5,  # At least 50% of keywords found
                    f"Found {len(keywords_found)}/{len(relevant_keywords)} keywords: {keywords_found}",
                    {"missing": [kw for kw in relevant_keywords if kw not in combined_text]}
                )
                
                # Check that captions are not generic/template-like
                generic_phrases = ["lorem ipsum", "example text", "placeholder", "your caption here"]
                no_generic = not any(phrase in combined_text for phrase in generic_phrases)
                
                self.log_result(
                    "Captions are not generic templates",
                    no_generic,
                    "No template/placeholder text found" if no_generic else "Found generic text",
                    None
                )
                
                # Check emoji usage for Instagram
                has_emojis = any(ord(c) > 127 for c in all_captions)
                self.log_result(
                    "Instagram captions include emojis",
                    has_emojis,
                    "Emojis found in captions" if has_emojis else "No emojis found",
                    None
                )
                
        except Exception as e:
            self.log_result(
                "AI response quality",
                False,
                f"Error: {str(e)[:100]}",
                None
            )

    # ==================== RUN ALL TESTS ====================
    
    async def run_all_tests(self):
        """Run all test suites."""
        print("\n" + "=" * 70)
        print("CONTENT GENERATION MODULE - COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        print(f"\nTarget: {self.base_url}")
        print(f"Test User: {TEST_USER_EMAIL}")
        print()
        
        async with httpx.AsyncClient() as client:
            # Check if server is running
            try:
                await client.get(f"{self.base_url}/docs", timeout=5.0)
            except httpx.ConnectError:
                print("❌ ERROR: Backend server is not running!")
                print(f"   Please start the server: python -m uvicorn main:app --port 8000")
                return
            
            # Authenticate
            print("🔐 Authenticating...")
            auth_success = await self.authenticate(client)
            if auth_success:
                print(f"✅ Authenticated as {TEST_USER_EMAIL}\n")
            else:
                print(f"⚠️  Could not authenticate - some tests will be skipped\n")
            
            # Run test suites
            await self.test_endpoints_exist(client)
            await self.test_authentication_required(client)
            await self.test_platforms_endpoint(client)
            await self.test_brand_context_endpoint(client)
            await self.test_content_generation_validation(client)
            await self.test_content_generation_success(client)
            await self.test_platform_specific_content(client)
            await self.test_ai_response_quality(client)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
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
    """Main entry point for tests."""
    suite = ContentGenerationTestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
