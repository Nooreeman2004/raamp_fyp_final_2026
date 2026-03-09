# Application Layer - Trend Detection Helpers
"""
Utility functions for trend detection enhancement.
Maintains backward compatibility - all functions return safe defaults.
"""
import logging
from typing import List
from bson import ObjectId
from bson.errors import InvalidId

logger = logging.getLogger(__name__)


# Synonym mapping for common business specialties
SPECIALTY_SYNONYMS = {
    # Beverages
    "bubble tea": ["boba", "boba tea", "pearl milk tea", "tapioca drinks", "milk tea"],
    "boba": ["bubble tea", "boba tea", "pearl milk tea"],
    "matcha": ["matcha latte", "green tea latte", "matcha drinks", "matcha tea"],
    "coffee": ["espresso", "latte", "cappuccino", "cold brew", "iced coffee"],
    "smoothies": ["fruit smoothies", "protein smoothies", "smoothie bowls"],
    
    # Food Categories
    "vegan": ["plant-based", "vegan food", "vegetarian", "vegan options"],
    "burgers": ["hamburgers", "cheeseburgers", "burger joint"],
    "pizza": ["pizzeria", "italian pizza", "pizza restaurant"],
    "sushi": ["japanese food", "sashimi", "rolls", "nigiri"],
    "ramen": ["japanese ramen", "noodles", "ramen bowls"],
    "tacos": ["mexican food", "mexican tacos", "taco restaurant"],
    "pasta": ["italian pasta", "spaghetti", "pasta dishes"],
    "seafood": ["fish", "shellfish", "seafood restaurant"],
    
    # Fashion
    "streetwear": ["street fashion", "urban wear", "casual streetwear"],
    "vintage": ["vintage clothing", "retro fashion", "vintage style"],
    "sustainable": ["sustainable fashion", "eco-friendly", "ethical fashion"],
    "luxury": ["luxury fashion", "designer", "high-end fashion"],
    
    # Fitness
    "yoga": ["yoga classes", "yoga studio", "hot yoga"],
    "crossfit": ["crossfit training", "functional fitness"],
    "pilates": ["pilates classes", "pilates studio"],
    
    # Beauty
    "skincare": ["skin care", "skincare products", "facial treatments"],
    "makeup": ["cosmetics", "makeup products", "beauty products"],
    "nails": ["nail art", "manicure", "nail salon"],
    
    # Tech
    "ai": ["artificial intelligence", "machine learning", "ai tools"],
    "crypto": ["cryptocurrency", "bitcoin", "blockchain"],
    "saas": ["software as a service", "cloud software", "saas products"],
}


async def resolve_niche_name(niche_input: str) -> str:
    """
    Resolve niche parameter to a valid niche name string.
    
    If niche_input looks like ObjectId, attempt to resolve from database.
    Otherwise, treat as plain string.
    
    Never crashes - always returns a safe string.
    
    Args:
        niche_input: Either a niche name string or MongoDB ObjectId
        
    Returns:
        Safe niche name string (lowercase, trimmed)
        
    Examples:
        "Fashion" → "fashion"
        "6925f43ab14d8328c6ede40c" → "fashion" (from DB) or "marketing" (fallback)
    """
    try:
        # Trim and validate input
        if not niche_input or not isinstance(niche_input, str):
            logger.warning("Invalid niche input: %s, using default", niche_input)
            return "marketing"
        
        niche_input = niche_input.strip()
        
        # Check if it looks like an ObjectId (24 hex characters)
        if len(niche_input) == 24 and all(c in '0123456789abcdefABCDEF' for c in niche_input):
            try:
                # Try to parse as ObjectId
                obj_id = ObjectId(niche_input)
                
                # Import here to avoid circular dependency
                from infrastructure.database.models.business_domain_model import BusinessDomainModel
                
                # Query database to get business name
                domain = await BusinessDomainModel.get(obj_id)
                
                if domain and domain.business:
                    resolved_name = domain.business.lower().strip()
                    logger.info(f"✅ Resolved ObjectId {niche_input} → {resolved_name}")
                    return resolved_name
                else:
                    logger.warning(f"⚠️ ObjectId {niche_input} not found in database, using fallback")
                    return "marketing"
                    
            except InvalidId:
                logger.warning(f"⚠️ Invalid ObjectId format: {niche_input}, treating as string")
                pass  # Fall through to treat as plain string
            except Exception as e:
                logger.error(f"❌ Error resolving ObjectId {niche_input}: {e}, using fallback")
                return "marketing"
        
        # Treat as plain string - normalize
        normalized = niche_input.lower().strip()
        logger.info(f"Using niche name as-is: {normalized}")
        return normalized if normalized else "marketing"
        
    except Exception as e:
        logger.error(f"❌ Unexpected error in resolve_niche_name: {e}, using fallback")
        return "marketing"


def expand_with_synonyms(keywords: List[str]) -> List[str]:
    """
    Expand keywords with synonyms for better trend detection.
    
    Maintains backward compatibility - never fails.
    
    Args:
        keywords: List of specialty keywords
        
    Returns:
        Expanded list with synonyms, deduplicated and lowercase
        
    Examples:
        ["bubble tea", "matcha"] → ["bubble tea", "boba", "boba tea", "matcha", "matcha latte", ...]
    """
    try:
        if not keywords or not isinstance(keywords, list):
            return []
        
        expanded = set()
        
        for keyword in keywords:
            if not keyword or not isinstance(keyword, str):
                continue
                
            # Add original keyword (normalized)
            normalized = keyword.lower().strip()
            if normalized:
                expanded.add(normalized)
                
                # Add synonyms if available
                if normalized in SPECIALTY_SYNONYMS:
                    synonyms = SPECIALTY_SYNONYMS[normalized]
                    expanded.update(synonyms)
                    logger.debug(f"Expanded '{normalized}' with {len(synonyms)} synonyms")
        
        result = list(expanded)
        logger.info(f"🔍 Keyword expansion: {len(keywords)} input → {len(result)} output")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in expand_with_synonyms: {e}, returning original keywords")
        # Safe fallback - return normalized originals
        try:
            return [k.lower().strip() for k in keywords if isinstance(k, str) and k.strip()]
        except:
            return []


def get_specialty_suggestions(business_niche: str) -> List[str]:
    """
    Get AI-powered specialty suggestions based on business niche.
    
    Returns common specialties for the given niche to help users during onboarding.
    
    Args:
        business_niche: Business category (e.g., "restaurants", "fashion")
        
    Returns:
        List of suggested specialty keywords
    """
    suggestions_map = {
        "restaurants": [
            "bubble tea", "sushi", "pizza", "burgers", "vegan", "ramen", 
            "tacos", "seafood", "pasta", "coffee", "desserts", "breakfast"
        ],
        "fashion": [
            "streetwear", "vintage", "sustainable", "luxury", "activewear",
            "accessories", "shoes", "denim", "formal wear", "casual"
        ],
        "fitness": [
            "yoga", "crossfit", "pilates", "boxing", "spinning", "personal training",
            "group classes", "weightlifting", "cardio", "martial arts"
        ],
        "beauty": [
            "skincare", "makeup", "nails", "hair styling", "spa", "facials",
            "massage", "waxing", "eyelashes", "brows"
        ],
        "tech": [
            "ai", "saas", "mobile apps", "web development", "crypto", "cloud",
            "cybersecurity", "data analytics", "automation", "iot"
        ],
        "retail": [
            "home decor", "furniture", "electronics", "books", "gifts",
            "toys", "jewelry", "art", "plants", "pets"
        ]
    }
    
    niche_lower = business_niche.lower().strip()
    return suggestions_map.get(niche_lower, [])
