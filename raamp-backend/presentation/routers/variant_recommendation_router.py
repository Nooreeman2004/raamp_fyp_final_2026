"""
Variant Recommendation Router
==============================
Analyzes content variants and recommends the best one(s) based on AI scoring.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import re


router = APIRouter(prefix="/api/variants", tags=["Variant Recommendations"])


class VariantInput(BaseModel):
    """Input model for a content variant"""
    id: int
    tone: str
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    variant_copy: Optional[str] = None  # Renamed from 'copy' to avoid shadowing built-in


class RecommendationRequest(BaseModel):
    """Request to get AI recommendations for variants"""
    variant_type: Literal["instagram", "whatsapp", "adcopy", "captions", "hashtags", "emails"]
    variants: List[VariantInput] = Field(..., min_items=1, max_items=3)


class RecommendationResponse(BaseModel):
    """Response with AI recommendation"""
    recommended_variant_id: int
    score: float
    reason: str


def calculate_engagement_score(variant: VariantInput, variant_type: str) -> tuple[float, str]:
    """
    Calculate engagement score for a variant based on best practices.
    Returns (score, reason) tuple.
    """
    score = 0.0
    reasons = []
    
    # Normalize variant_type for scoring logic
    effective_type = variant_type
    if variant_type == "captions":
        effective_type = "instagram"
    elif variant_type == "emails":
        effective_type = "adcopy"
    elif variant_type == "hashtags":
        # Specific hashtag scoring
        text = (variant.hashtags or "") + " " + (variant.variant_copy or "")
        hashtag_count = len(re.findall(r'#\w+', text))
        if 15 <= hashtag_count <= 25:
            score += 40
            reasons.append("broad reach")
        elif hashtag_count > 5:
            score += 20
            reasons.append("niche targeting")
        
        # Diversity check
        if len(set(re.findall(r'#\w+', text))) > 10:
            score += 20
            reasons.append("diverse strategy")
        
        reason = "AI detected: " + ", ".join(reasons[:3]) if reasons else "Strategic hashtag mix"
        return float(score), reason

    if effective_type == "instagram":
        text = f"{variant.caption or ''} {variant.hashtags or ''}"
        
        # Emoji usage (engagement booster)
        emoji_count = len(re.findall(r'[^\w\s,]', text))
        if emoji_count >= 3 and emoji_count <= 8:
            score += 25
            reasons.append("optimal emoji usage")
        elif emoji_count > 0:
            score += 15
            reasons.append("includes emojis")
        
        # Call-to-action presence
        cta_patterns = ['tell us', 'comment', 'tag', 'share', 'click', 'tap', 'dm', 'link in bio', '👇', 'drop', 'let us know']
        if any(pattern in text.lower() for pattern in cta_patterns):
            score += 30
            reasons.append("strong call-to-action")
        
        # Caption length (150-200 chars is optimal)
        caption_len = len(variant.caption or '')
        if 100 <= caption_len <= 250:
            score += 20
            reasons.append("optimal caption length")
        elif caption_len > 0:
            score += 10
        
        # Hashtag count (15-20 is optimal, 30 max)
        hashtag_count = len(re.findall(r'#\w+', variant.hashtags or ''))
        if 10 <= hashtag_count <= 20:
            score += 25
            reasons.append("optimal hashtag count")
        elif hashtag_count >= 5:
            score += 15
            reasons.append("good hashtag coverage")
        
    elif variant_type == "whatsapp":
        text = str(variant.copy or '')
        
        # Personalization tokens
        if '[Name]' in text or '[name]' in text.lower():
            score += 30
            reasons.append("personalized messaging")
        
        # Clear offer/discount
        if any(word in text.lower() for word in ['%', 'off', 'discount', 'deal', 'offer', 'sale']):
            score += 25
            reasons.append("compelling offer")
        
        # Link/CTA presence
        if '[Link]' in text or '[link]' in text.lower() or 'shop now' in text.lower() or 'order now' in text.lower():
            score += 20
            reasons.append("clear call-to-action")
        
        # Optimal length (50-150 chars for WhatsApp)
        if 50 <= len(text) <= 200:
            score += 25
            reasons.append("optimal message length")
        elif len(text) > 0:
            score += 10
        
    elif variant_type == "adcopy":
        text = variant.variant_copy or ''
        
        # Urgency/FOMO indicators
        urgency_words = ['now', 'today', 'limited', 'don\'t miss', 'hurry', 'expires', 'only']
        if any(word in text.lower() for word in urgency_words):
            score += 30
            reasons.append("creates urgency")
        
        # Question-based engagement
        if '?' in text:
            score += 20
            reasons.append("engages with question")
        
        # Benefit-focused language
        benefit_words = ['boost', 'improve', 'better', 'best', 'fresh', 'new', 'organic', 'pure', 'natural']
        if any(word in text.lower() for word in benefit_words):
            score += 25
            reasons.append("highlights benefits")
        
        # Optimal ad copy length (60-150 chars)
        if 60 <= len(text) <= 150:
            score += 25
            reasons.append("optimal ad length")
        elif len(text) > 0:
            score += 10
    
    # Tone appropriateness bonus
    tone_keywords = {
        'vibrant': ['!', '☀️', '✨', 'love'],
        'professional': ['professional', 'quality', 'pure'],
        'urgent': ['now', 'limited', 'hurry', 'don\'t miss'],
        'direct': ['order', 'click', 'shop', 'buy'],
        'playful': ['😊', '🎉', 'fun', 'favorite'],
        'personalized': ['[Name]', 'you', 'your'],
        'emotional': ['feel', 'love', 'enjoy', 'delight']
    }
    
    tone_lower = variant.tone.lower()
    for tone_type, keywords in tone_keywords.items():
        if tone_type in tone_lower:
            text_all = f"{variant.caption or ''} {variant.hashtags or ''} {variant.copy or ''}".lower()
            if any(kw.lower() in text_all for kw in keywords):
                score += 10
                reasons.append(f"tone matches {tone_type} style")
                break
    
    # Generate reason string
    reason = "AI detected: " + ", ".join(reasons[:3]) if reasons else "Good baseline variant"
    
    return score, reason


@router.post("/recommend", response_model=RecommendationResponse)
async def get_variant_recommendation(request: RecommendationRequest):
    """
    Analyze variants and return AI-powered recommendation.
    
    Scoring criteria:
    - Instagram: Emoji usage, CTAs, caption length, hashtag optimization
    - WhatsApp: Personalization, offers, CTA clarity, message length
    - Ad Copy: Urgency, engagement, benefits, optimal length
    """
    if not request.variants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one variant is required"
        )
    
    # Calculate scores for all variants
    scored_variants = []
    for variant in request.variants:
        score, reason = calculate_engagement_score(variant, request.variant_type)
        scored_variants.append({
            "variant": variant,
            "score": score,
            "reason": reason
        })
    
    # Find highest scoring variant
    best_variant = max(scored_variants, key=lambda x: x["score"])
    
    return RecommendationResponse(
        recommended_variant_id=best_variant["variant"].id,
        score=best_variant["score"],
        reason=best_variant["reason"]
    )
