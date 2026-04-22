"""
Pydantic schemas for Brand Alignment Settings
"""
from pydantic import BaseModel, Field, validator, model_validator
import re
from typing import Optional, List


class ToneOfVoiceProfile(BaseModel):
    """
    Structured tone-of-voice system (strict but user-friendly).

    Answers:
    - Who are we? (personality)
    - Who are we talking to? (audience)
    - How do we speak? (language rules)
    - Where are we speaking? (platform)
    - What are we saying? (content type)
    """

    personality: str = Field(..., min_length=1, description="Brand personality traits and vibe")
    audience: str = Field(..., min_length=1, description="Target audience description")
    language_rules: str = Field(..., min_length=1, description="Do/don't rules, style constraints, examples")
    platforms: List[str] = Field(default_factory=list, description="Where this will be used (e.g., instagram, facebook)")
    content_types: List[str] = Field(default_factory=list, description="What types of content (e.g., caption, reply, story)")

    @staticmethod
    def _word_count(s: str) -> int:
        return len([w for w in re.split(r"\s+", (s or "").strip()) if w])

    @classmethod
    def _basic_clean(cls, v: str) -> str:
        return (v or "").strip()

    @validator("personality", "audience", "language_rules")
    @classmethod
    def _validate_required_quality(cls, v: str):
        v = cls._basic_clean(v)
        if not v:
            raise ValueError("Required field cannot be empty")
        # Block single-word / ultra-short junk without being overly strict
        if cls._word_count(v) < 2 and len(v) < 12:
            raise ValueError("Too vague. Use at least 2 words (or a short phrase with specifics).")
        if len(v) < 12:
            raise ValueError("Too short. Add a bit more detail (at least ~12 characters).")
        return v

    @validator("platforms", "content_types", pre=True)
    @classmethod
    def _coerce_str_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            # Accept comma-separated strings as a friendly input format
            parts = [p.strip() for p in v.split(",")]
            return [p for p in parts if p]
        return v

    def quality_score(self) -> int:
        """
        Returns 0..100 score. Used for both UI hinting and strict server acceptance.
        We keep it forgiving: short but concrete entries can still pass.
        """
        score = 0

        def add_for_text(s: str, *, min_words: int, max_points: int) -> int:
            s = (s or "").strip()
            if not s:
                return 0
            wc = self._word_count(s)
            pts = 0
            if wc >= min_words:
                pts += max_points // 2
            if len(s) >= 60:
                pts += max_points // 2
            # Bonus if contains "do/don't" style constraints or examples
            if re.search(r"\b(do not|don't|avoid|must|always|never|example|e\.g\.)\b", s, re.I):
                pts += 6
            return min(max_points, pts)

        score += add_for_text(self.personality, min_words=3, max_points=28)
        score += add_for_text(self.audience, min_words=4, max_points=28)
        score += add_for_text(self.language_rules, min_words=6, max_points=34)

        if self.platforms:
            score += 5
        if self.content_types:
            score += 5

        return max(0, min(100, score))


class BrandAlignmentRequest(BaseModel):
    """Request schema for brand alignment settings - ALL FIELDS REQUIRED"""
    
    brand_logo_url: str = Field(..., min_length=1, description="Firebase URL of uploaded brand logo")
    primary_color: str = Field(..., description="Primary brand color (hex code)")
    secondary_color: str = Field(..., description="Secondary brand color (hex code)")
    tagline: str = Field(..., min_length=1, max_length=100, description="Restaurant tagline")
    # Backward compatible: existing services read tone_of_voice string.
    # New UI should send tone_profile; server will generate/accept tone_of_voice.
    tone_of_voice: Optional[str] = Field(None, min_length=1, description="Tone of voice for AI content (legacy string)")
    tone_profile: Optional[ToneOfVoiceProfile] = Field(None, description="Structured tone-of-voice system")
    restaurant_theme: str = Field(..., min_length=1, description="Restaurant theme/ambiance - REQUIRED")
    brand_colors: list[str] = Field(default_factory=list, description="List of brand hex colors")
    palette_source: str = Field(default="custom", description="Source of the palette (template, logo, or manual)")
    
    @validator('primary_color', 'secondary_color')
    @classmethod
    def validate_hex_color(cls, v):
        """Validate hex color format"""
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('Color must be in hex format (#RRGGBB)')
        return v.upper()

    @validator("brand_colors")
    @classmethod
    def validate_brand_colors(cls, v: list[str]):
        """Validate each palette color is hex (#RRGGBB). Any color is allowed, format must be correct."""
        if v is None:
            return []
        cleaned: list[str] = []
        for c in v:
            if not c:
                continue
            c = c.strip()
            if not re.match(r"^#[0-9A-Fa-f]{6}$", c):
                raise ValueError("All brand_colors must be in hex format (#RRGGBB)")
            cleaned.append(c.upper())
        return cleaned
    
    @validator('tagline')
    @classmethod
    def validate_tagline(cls, v):
        """Validate tagline"""
        if not v or not v.strip():
            raise ValueError('Tagline cannot be empty')
        return v.strip()
    
    @model_validator(mode="after")
    def validate_tone_inputs(self):
        """
        Enforce a strict-but-friendly rule:
        - tone_profile is preferred.
        - if tone_profile absent, tone_of_voice must be present and non-vague.
        - if tone_profile present, it must pass quality threshold.
        """
        if not self.tone_profile and not (self.tone_of_voice and self.tone_of_voice.strip()):
            raise ValueError("Tone of voice is required (provide tone_profile or tone_of_voice).")

        if self.tone_profile:
            score = self.tone_profile.quality_score()
            # Friendly threshold: blocks only truly vague inputs
            if score < 45:
                raise ValueError(
                    "Tone of voice is too vague. Add more specifics (personality, audience, and language rules)."
                )
        else:
            tone = (self.tone_of_voice or "").strip()
            # Block single-word tone like "friendly"
            if len(tone) < 12 or ToneOfVoiceProfile._word_count(tone) < 2:
                raise ValueError("Tone of voice is too vague. Use at least a short, specific phrase.")
            self.tone_of_voice = tone

        return self
    
    @validator('restaurant_theme')
    @classmethod
    def validate_theme(cls, v):
        """Validate restaurant theme"""
        if not v or not v.strip():
            raise ValueError('Restaurant theme cannot be empty')
        return v.strip()
    
    @validator('brand_logo_url')
    @classmethod
    def validate_logo_url(cls, v):
        """Validate logo URL"""
        if not v or not v.strip():
            raise ValueError('Brand logo URL is required')
        return v.strip()


class BrandAlignmentResponse(BaseModel):
    """Response schema for brand alignment settings"""
    
    brand_logo_url: str
    primary_color: str
    secondary_color: str
    tagline: str
    tone_of_voice: str
    tone_profile: Optional[ToneOfVoiceProfile] = None
    restaurant_theme: str
    brand_colors: list[str] = []
    palette_source: str = "custom"
    updated_at: str
    
    class Config:
        from_attributes = True
