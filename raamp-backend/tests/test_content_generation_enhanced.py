"""
Enhanced Content Generation Service Unit Tests
==============================================
Simplified integration tests for prompt engineering improvements.
Tests validate that improvements are present in prompts and service methods.
"""

import pytest
import re
from application.services.content_generation_service import ContentGenerationService


class TestPromptEnhancements:
    """Test that prompt engineering improvements are present in the service"""
    
    def test_chain_of_thought_analysis_in_prompt(self):
        """Test that Chain-of-Thought strategic analysis section exists in POST prompt"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        # Should contain strategic analysis keywords
        assert "STRATEGIC ANALYSIS" in prompt or "Chain-of-Thought" in prompt, "Should have strategic analysis section"
        assert "Audience Psychology" in prompt, "Should analyze audience psychology"
        assert "Content Goal Classification" in prompt, "Should classify content goals"
        assert "Hook Strategy Selection" in prompt, "Should have hook strategy selection"
        assert "Call-to-Action Engineering" in prompt, "Should have CTA engineering"
    
    def test_seasonal_hashtag_optimization_in_prompt(self):
        """Test that seasonal/trending hashtag guidance is in the prompt"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        # Should contain seasonal hashtag guidance
        assert "Seasonal" in prompt or "SEASONAL" in prompt, "Should have seasonal hashtag section"
        assert "March" in prompt or "Spring" in prompt, "Should have month examples"
        assert "Trending" in prompt or "TRENDING" in prompt, "Should have trending hashtag guidance"
        assert "#Spring" in prompt or "seasonal" in prompt.lower(), "Should have seasonal tag examples"
    
    def test_brand_voice_framework_in_prompt(self):
        """Test that brand voice archetypes are defined in the prompt"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        # Should contain brand voice archetypes
        assert "BRAND VOICE" in prompt or "Brand Voice" in prompt, "Should have brand voice section"
        assert "Innovator" in prompt, "Should have Innovator archetype"
        assert "Nurturer" in prompt, "Should have Nurturer archetype"
        assert "Creator" in prompt, "Should have Creator archetype"
        assert "Expert" in prompt, "Should have Expert archetype"
        assert "Rebel" in prompt, "Should have Rebel archetype"
        assert "Entertainer" in prompt, "Should have Entertainer archetype"
    
    def test_negative_examples_in_prompt(self):
        """Test that negative examples (what NOT to do) are included"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        # Should contain negative examples
        assert "BAD" in prompt or "MISTAKE" in prompt or "What NOT To Do" in prompt, "Should have negative examples"
        assert "FAILS" in prompt or "WHY THIS FAILS" in prompt, "Should explain why bad examples fail"
        assert "❌" in prompt, "Should use visual indicators for bad examples"


class TestOutputConstraints:
    """Test that output constraints are defined in prompts"""
    
    def test_post_output_constraints_defined(self):
        """Test POST prompt has strict output constraints"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        assert "OUTPUT CONSTRAINTS" in prompt, "Should have output constraints section"
        assert "125-150 words" in prompt or "word count" in prompt.lower(), "Should specify word count"
        assert "800-1,200 characters" in prompt or "character" in prompt.lower(), "Should specify character count"
        assert "40-60 characters" in prompt, "Should specify first line hook length"
    
    def test_story_output_constraints_defined(self):
        """Test STORY prompt has different constraints than POST"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_STORY
        
        assert "20-50 character" in prompt or "20-50 char" in prompt, "Story should have 20-50 char limit"
        assert "STORY" in prompt, "Should be labeled as story prompt"
        assert "interactive" in prompt.lower() or "Interactive" in prompt, "Should mention interactive elements"
    
    def test_reel_output_constraints_defined(self):
        """Test REEL prompt has video-specific constraints"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_REEL
        
        assert "100-150 char" in prompt or "REEL" in prompt, "Should be labeled as reel prompt"
        assert "video" in prompt.lower() or "Video" in prompt, "Should mention video concepts"
        assert "first 3 words" in prompt.lower() or "hook" in prompt.lower(), "Should emphasize hook importance"


class TestFewShotExamples:
    """Test that few-shot learning examples are present"""
    
    def test_excellent_examples_present(self):
        """Test that EXCELLENT examples are provided for learning"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        assert "EXCELLENT" in prompt or "✅" in prompt, "Should have excellent examples"
        assert "WHY THIS WORKS" in prompt or "Analysis" in prompt, "Should explain why examples work"
    
    def test_bad_examples_present(self):
        """Test that BAD examples are provided to avoid"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        assert "BAD" in prompt or "❌" in prompt, "Should have bad examples"
        assert "WHY THIS FAILS" in prompt or "fails" in prompt.lower(), "Should explain why examples fail"
    
    def test_examples_have_analysis(self):
        """Test that examples include detailed analysis"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        # Count example blocks
        excellent_count = prompt.count("EXCELLENT") + prompt.count("✅ GOOD")
        bad_count = prompt.count("BAD") + prompt.count("❌")
        
        assert excellent_count >= 1, "Should have at least 1 excellent example"
        assert bad_count >= 1, "Should have at least 1 bad example"


class TestHashtagGuidance:
    """Test hashtag stratification and seasonal guidance"""
    
    def test_hashtag_size_stratification_explained(self):
        """Test that hashtag size mixing is explained"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        assert "Large" in prompt and ("hashtag" in prompt or ">1M" in prompt), "Should explain large hashtags"
        assert "Medium" in prompt and ("hashtag" in prompt or "100K" in prompt), "Should explain medium hashtags"
        assert "Small" in prompt and ("hashtag" in prompt or "<100K" in prompt), "Should explain small hashtags"
    
    def test_banned_hashtags_documented(self):
        """Test that banned/spam hashtags are documented"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        assert "#like4like" in prompt or "like4like" in prompt, "Should mention banned tags"
        assert "banned" in prompt.lower() or "avoid" in prompt.lower(), "Should warn about banned tags"
    
    def test_seasonal_hashtag_guide_exists(self):
        """Test that monthly seasonal hashtag guide exists"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        # Should have monthly breakdown
        months = ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
        
        found_months = sum(1 for month in months if month in prompt)
        assert found_months >= 6, f"Should have at least 6 months in seasonal guide, found {found_months}"


class TestBrandVoiceExamples:
    """Test brand voice archetype examples"""
    
    def test_innovator_archetype_defined(self):
        """Test Innovator archetype has personality, values, and voice"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        # Find Innovator section
        assert "Innovator" in prompt, "Should have Innovator archetype"
        
        # Should have key components
        innovator_section_start = prompt.find("Innovator")
        innovator_section = prompt[innovator_section_start:innovator_section_start + 1000]
        
        assert "Personality:" in innovator_section or "forward-thinking" in innovator_section.lower(), "Should define personality"
        assert "Values:" in innovator_section or "innovation" in innovator_section.lower(), "Should define values"
        assert "Voice:" in innovator_section or "Example:" in innovator_section, "Should have voice examples"
    
    def test_nurturer_archetype_defined(self):
        """Test Nurturer archetype has complete framework"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        assert "Nurturer" in prompt, "Should have Nurturer archetype"
        
        nurturer_section_start = prompt.find("Nurturer")
        nurturer_section = prompt[nurturer_section_start:nurturer_section_start + 1000]
        
        assert "caring" in nurturer_section.lower() or "supportive" in nurturer_section.lower(), "Should have caring personality"
        assert "well-being" in nurturer_section.lower() or "wellness" in nurturer_section.lower(), "Should mention wellness values"
    
    def test_brand_voice_consistency_examples(self):
        """Test that voice consistency examples exist"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        assert "Consistent Voice" in prompt or "GOOD - Consistent" in prompt or "Voice Consistency" in prompt, "Should have consistency examples"
        assert "Inconsistent" in prompt or "BAD - Inconsistent" in prompt, "Should show inconsistent voice example"


class TestPsychologicalTriggers:
    """Test psychological trigger guidance"""
    
    def test_fomo_triggers_explained(self):
        """Test FOMO triggers are explained"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        assert "FOMO" in prompt, "Should explain FOMO triggers"
        assert "Limited time" in prompt or "Scarcity" in prompt, "Should have scarcity language"
    
    def test_social_proof_triggers_explained(self):
        """Test social proof triggers are explained"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        assert "Social Proof" in prompt or "social proof" in prompt, "Should explain social proof"
        assert "Join" in prompt or "customers" in prompt, "Should have social proof examples"
    
    def test_multiple_trigger_types_documented(self):
        """Test that multiple psychological trigger types are documented"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        triggers = ["FOMO", "Scarcity", "Urgency", "Social Proof", "Authority", "Transformation"]
        found_triggers = sum(1 for trigger in triggers if trigger in prompt)
        
        assert found_triggers >= 4, f"Should document at least 4 trigger types, found {found_triggers}"


class TestCommonMistakesSection:
    """Test that common mistakes are documented"""
    
    def test_common_mistakes_section_exists(self):
        """Test that a common mistakes section exists"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        assert "COMMON" in prompt and "MISTAKE" in prompt, "Should have common mistakes section"
        assert "❌" in prompt, "Should use visual indicators for mistakes"
    
    def test_mistake_examples_have_fixes(self):
        """Test that mistakes include fixes"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        if "COMMON" in prompt and "MISTAKE" in prompt:
            # Should have FIX sections
            assert "FIX:" in prompt or "Fix:" in prompt or "GOOD Example" in prompt, "Mistakes should include fixes"
    
    def test_quality_checklist_exists(self):
        """Test that a quality checklist exists"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_POST
        
        assert "QUALITY CHECKLIST" in prompt or "checklist" in prompt.lower(), "Should have quality checklist"
        assert "[ ]" in prompt or "verify" in prompt.lower(), "Should have checklist items"


class TestPlatformSpecificPrompts:
    """Test that different platform types have different prompts"""
    
    def test_get_system_prompt_method_exists(self):
        """Test that _get_system_prompt method exists"""
        service = ContentGenerationService()
        
        assert hasattr(service, '_get_system_prompt'), "Should have _get_system_prompt method"
    
    def test_different_prompts_for_different_platforms(self):
        """Test that POST, STORY, REEL have different prompts"""
        service = ContentGenerationService()
        
        post_prompt = service._get_system_prompt("post")
        story_prompt = service._get_system_prompt("story")
        reel_prompt = service._get_system_prompt("reel")
        
        # They should be different
        assert post_prompt != story_prompt, "POST and STORY prompts should be different"
        assert post_prompt != reel_prompt, "POST and REEL prompts should be different"
        assert story_prompt != reel_prompt, "STORY and REEL prompts should be different"
    
    def test_story_prompt_emphasizes_brevity(self):
        """Test STORY prompt emphasizes short text"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_STORY
        
        assert "20-50" in prompt or "short" in prompt.lower(), "STORY should emphasize brevity"
        assert "NOT 125-150" in prompt or "shorter" in prompt.lower(), "Should clarify STORY is different from POST"
    
    def test_reel_prompt_emphasizes_video(self):
        """Test REEL prompt emphasizes video concepts"""
        service = ContentGenerationService()
        prompt = service.SYSTEM_PROMPT_REEL
        
        assert "video" in prompt.lower() or "Video" in prompt, "REEL should mention video"
        assert "hook" in prompt.lower() or "Hook" in prompt, "REEL should emphasize hooks"
        assert "first" in prompt.lower(), "REEL should mention first few seconds/words"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
