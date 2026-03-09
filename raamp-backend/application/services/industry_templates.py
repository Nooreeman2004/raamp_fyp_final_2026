"""
Industry-Specific Content Templates
====================================
Maps business domains to optimized content patterns, hooks, CTAs, and hashtags.
Integrated with RAAMP's content generation service for industry-relevant AI content.
"""

from typing import Optional, Dict, List, Any


# ============================================================================
# INDUSTRY TEMPLATE DEFINITIONS
# ============================================================================

INDUSTRY_TEMPLATES = {
    "Restaurants": {
        "description": "Food and beverage establishments, cafes, fine dining, fast food",
        "hooks": [
            "This [dish] sold out in 2 hours... 🍽️",
            "Our secret ingredient? {bold_claim}",
            "Hungry? This will change everything 👀",
            "POV: You just discovered the best [cuisine] in [city]",
            "Warning: This will make you crave [dish] instantly 🤤"
        ],
        "cta_templates": [
            "Tag your foodie friend who needs to try this!",
            "Save this spot for your next date night 💕",
            "Drop a 🍕 if you're hungry now",
            "Double tap if you'd order this right now",
            "Share with someone who loves [cuisine type]"
        ],
        "hashtag_bank": {
            "large": ["#FoodPorn", "#FoodPhotography", "#Food", "#InstaFood", "#Foodie"],
            "medium": ["#FoodBlogger", "#RestaurantLife", "#ChefLife", "#FoodLover", "#Yummy"],
            "small": ["#LocalEats", "#FoodieSpot", "#HiddenGem", "#FoodComa", "#FoodHeaven"],
            "trending_categories": ["DineLocal", "FoodTok", "FoodieFriday", "CheatMeal"]
        },
        "content_types": {
            "menu_drop": "New menu item announcement with mouth-watering description",
            "special_announcement": "Limited-time offers, seasonal specials, happy hour",
            "behind_the_scenes": "Chef at work, kitchen prep, ingredient sourcing",
            "customer_review": "User-generated content, testimonials, food reactions",
            "chef_story": "Meet the chef, culinary philosophy, signature dishes",
            "ingredient_spotlight": "Fresh ingredients, local sourcing, quality focus"
        },
        "tone_modifiers": {
            "casual_dining": "Friendly, approachable, family-oriented",
            "fine_dining": "Sophisticated, elegant, experience-focused",
            "fast_casual": "Quick, convenient, value-driven",
            "cafe": "Cozy, community-focused, lifestyle-oriented"
        },
        "engagement_boosters": [
            "Ask: 'What's your go-to order here?'",
            "Poll: 'Appetizer or Dessert first?'",
            "Challenge: 'Tag someone who can't resist [dish]'",
            "Save-worthy: 'Our full menu guide (save for later!)'"
        ]
    },
    
    "Fashion": {
        "description": "Clothing brands, apparel, accessories, footwear, fashion retail",
        "hooks": [
            "This outfit broke the internet 🔥",
            "Sold out in 30 minutes (but we restocked 👀)",
            "POV: You found your new favorite brand",
            "The [item] everyone's asking about...",
            "Style secret the influencers don't want you to know ✨"
        ],
        "cta_templates": [
            "Tag someone with this style 👗",
            "Save this fit for inspo!",
            "Drop a ❤️ if you'd wear this",
            "Double tap if this is YOUR vibe",
            "Comment 'SHOP' for the link"
        ],
        "hashtag_bank": {
            "large": ["#Fashion", "#Style", "#OOTD", "#InstaFashion", "#FashionBlogger"],
            "medium": ["#StyleInspo", "#FashionGram", "#OutfitOfTheDay", "#Fashionista", "#StreetStyle"],
            "small": ["#SustainableFashion", "#LocalBrand", "#IndieFashion", "#SlowFashion", "#EthicalFashion"],
            "trending_categories": ["FashionTok", "StyleChallenge", "GetReadyWithMe", "FashionHaul"]
        },
        "content_types": {
            "outfit_post": "Complete look showcase with styling details",
            "styling_tips": "How to wear, mix-and-match, capsule wardrobe",
            "new_collection": "Launch announcement, lookbook preview, collection story",
            "behind_the_design": "Design process, fabric selection, craftsmanship",
            "customer_styling": "Real customer photos, UGC, testimonials",
            "trend_alert": "What's trending, how to style trending pieces"
        },
        "tone_modifiers": {
            "luxury": "Exclusive, sophisticated, aspirational",
            "streetwear": "Edgy, bold, youth-focused, trend-driven",
            "sustainable": "Conscious, ethical, quality-over-quantity",
            "fast_fashion": "Trendy, affordable, accessible, viral"
        },
        "engagement_boosters": [
            "Ask: 'How would you style this?'",
            "Poll: 'Dress up or dress down?'",
            "Challenge: 'Recreate this look and tag us!'",
            "Save-worthy: 'Ultimate styling guide for [item]'"
        ]
    },
    
    "E-commerce": {
        "description": "Online retail, marketplaces, direct-to-consumer brands",
        "hooks": [
            "Just dropped: The [product] everyone's been waiting for 📦",
            "This product has 1,000+ 5-star reviews. Here's why...",
            "POV: You found THE solution to [pain point]",
            "Sold out 3 times. Back in stock NOW 👀",
            "Before you buy [competitor], see this..."
        ],
        "cta_templates": [
            "Tag someone who needs this in their life",
            "Save for when you're ready to upgrade!",
            "Drop a 🛒 if you're adding to cart",
            "Comment 'LINK' to shop now",
            "Share with your [target persona] friend"
        ],
        "hashtag_bank": {
            "large": ["#OnlineShopping", "#ShopSmall", "#SmallBusiness", "#SupportLocal", "#Shop"],
            "medium": ["#OnlineStore", "#ShopNow", "#ProductReview", "#UnboxingExperience", "#CustomerLove"],
            "small": ["#DirectToConsumer", "#IndependentBrand", "#ShopIndependent", "#EcommerceBrand"],
            "trending_categories": ["AmazonFinds", "TikTokMadeMeBuyIt", "ProductReview", "UnboxingHaul"]
        },
        "content_types": {
            "product_drop": "New product launch with features and benefits",
            "customer_review": "Testimonials, before/after, unboxing reactions",
            "how_to_use": "Tutorials, tips, best practices, use cases",
            "behind_the_brand": "Founder story, mission, values, why we exist",
            "comparison": "Us vs. competitor, feature comparison, value prop",
            "sale_announcement": "Limited-time offers, flash sales, discounts"
        },
        "tone_modifiers": {
            "premium": "Quality-focused, investment-worthy, long-term value",
            "budget_friendly": "Affordable, accessible, value-for-money",
            "innovative": "Cutting-edge, problem-solving, game-changing",
            "lifestyle": "Aspirational, experience-focused, community-driven"
        },
        "engagement_boosters": [
            "Ask: 'Which color would you choose?'",
            "Poll: 'Option A or Option B?'",
            "Challenge: 'Show us how you use [product]!'",
            "Save-worthy: 'Complete guide to [product category]'"
        ]
    },
    
    "Tech Startup": {
        "description": "SaaS products, mobile apps, software development, tech services",
        "hooks": [
            "This app just changed the [industry] game forever 🚀",
            "We built the [feature] that [big company] couldn't",
            "POV: You discovered the tool everyone will be using in 2027",
            "[X] hours saved per week. Here's how...",
            "Your [workflow] is about to get 10x faster ⚡"
        ],
        "cta_templates": [
            "Tag a teammate who needs to see this",
            "Save this for your next project!",
            "Drop a 💻 if you're trying this",
            "Comment 'DEMO' for early access",
            "Share with your [professional role] network"
        ],
        "hashtag_bank": {
            "large": ["#Tech", "#Technology", "#Startup", "#Innovation", "#SaaS"],
            "medium": ["#TechStartup", "#Productivity", "#DigitalTransformation", "#Software", "#AI"],
            "small": ["#StartupLife", "#TechCommunity", "#ProductivityHacks", "#WorkSmarter", "#Automation"],
            "trending_categories": ["AITools", "ProductivityTech", "StartupStory", "TechReview"]
        },
        "content_types": {
            "feature_announcement": "New feature launch, updates, improvements",
            "use_case": "How customers use it, success stories, ROI demos",
            "tutorial": "How-to guides, tips, best practices, workflows",
            "behind_the_code": "Engineering insights, tech stack, architecture",
            "founder_story": "Why we built this, problem we're solving, vision",
            "integration": "New integrations, partnerships, ecosystem expansion"
        },
        "tone_modifiers": {
            "enterprise": "Professional, scalable, secure, compliance-focused",
            "startup": "Scrappy, innovative, fast-moving, disruptive",
            "developer_focused": "Technical, detailed, open-source, community-driven",
            "consumer_app": "User-friendly, accessible, lifestyle-enhancing"
        },
        "engagement_boosters": [
            "Ask: 'What feature should we build next?'",
            "Poll: 'Feature X or Feature Y priority?'",
            "Challenge: 'Share your workflow improvement!'",
            "Save-worthy: 'Complete guide to [tool category]'"
        ]
    },
    
    "Healthcare": {
        "description": "Medical services, wellness, fitness, health products, telehealth",
        "hooks": [
            "This wellness tip changed my morning routine 🌅",
            "Doctors recommend this simple [health practice]...",
            "POV: You finally found a solution that works",
            "Your body will thank you for this 💪",
            "The [health myth] experts want you to stop believing"
        ],
        "cta_templates": [
            "Tag someone on their wellness journey",
            "Save this for your health goals!",
            "Drop a 💚 if you're trying this",
            "Double tap if this resonates",
            "Share with someone who needs to hear this"
        ],
        "hashtag_bank": {
            "large": ["#Health", "#Wellness", "#Fitness", "#HealthyLiving", "#WellnessJourney"],
            "medium": ["#HealthTips", "#WellnessCommunity", "#HealthyLifestyle", "#SelfCare", "#MentalHealth"],
            "small": ["#HolisticHealth", "#WellnessCoach", "#PreventiveCare", "#HealthOptimization"],
            "trending_categories": ["WellnessTok", "HealthHacks", "FitnessMotivation", "MindfulLiving"]
        },
        "content_types": {
            "health_tip": "Daily tips, wellness advice, preventive care",
            "myth_buster": "Debunking health myths, evidence-based facts",
            "success_story": "Patient testimonials, transformation stories, progress",
            "expert_advice": "Doctor Q&A, professional insights, medical facts",
            "wellness_routine": "Morning routines, self-care practices, habits",
            "service_intro": "New services, treatments, technology, capabilities"
        },
        "tone_modifiers": {
            "medical": "Professional, evidence-based, authoritative, trustworthy",
            "wellness": "Holistic, compassionate, empowering, supportive",
            "fitness": "Motivational, energetic, goal-oriented, inspiring",
            "mental_health": "Empathetic, validating, stigma-reducing, accessible"
        },
        "engagement_boosters": [
            "Ask: 'What's your wellness goal this month?'",
            "Poll: 'Morning workout or evening workout?'",
            "Challenge: 'Join our 7-day wellness challenge!'",
            "Save-worthy: 'Complete guide to [health topic]'"
        ],
        "compliance_notes": "Avoid medical claims, always include disclaimers, focus on wellness over treatment"
    },
    
    "Education": {
        "description": "Online courses, e-learning platforms, tutoring, educational content",
        "hooks": [
            "This learning method cut study time in HALF 📚",
            "The skill everyone will need in 2027 (and how to learn it)",
            "POV: You finally understand [complex topic]",
            "Teacher's secret: How to actually retain what you learn",
            "This changed how I approach [subject] forever 🎓"
        ],
        "cta_templates": [
            "Tag a student who needs this!",
            "Save this study tip for exams",
            "Drop a 📖 if you're enrolling",
            "Comment 'LEARN' for course details",
            "Share with your study group"
        ],
        "hashtag_bank": {
            "large": ["#Education", "#Learning", "#OnlineLearning", "#StudyTips", "#Education"],
            "medium": ["#Elearning", "#StudyMotivation", "#LearnOnline", "#SkillDevelopment", "#StudentLife"],
            "small": ["#LifelongLearning", "#EdTech", "#OnlineCourse", "#SelfEducation", "#LearningCommunity"],
            "trending_categories": ["StudyTok", "LearnOn", "SkillUp", "EducationForAll"]
        },
        "content_types": {
            "course_preview": "Free lesson, course trailer, curriculum overview",
            "student_success": "Success stories, testimonials, job placements",
            "learning_tip": "Study techniques, memory hacks, productivity tips",
            "expert_interview": "Industry expert Q&A, career advice, trends",
            "free_resource": "Downloadable guides, cheat sheets, templates",
            "course_launch": "New course announcement, early bird offers, bonuses"
        },
        "tone_modifiers": {
            "academic": "Scholarly, rigorous, research-based, credible",
            "practical": "Applied, hands-on, career-focused, results-driven",
            "motivational": "Inspiring, empowering, growth-mindset, encouraging",
            "beginner_friendly": "Accessible, welcoming, step-by-step, patient"
        },
        "engagement_boosters": [
            "Ask: 'What skill are you learning right now?'",
            "Poll: 'Video lessons or written guides?'",
            "Challenge: 'Share your learning wins this week!'",
            "Save-worthy: 'Complete roadmap to learn [skill]'"
        ]
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def infer_business_domain(business_type: Optional[str]) -> str:
    """
    Infer the business domain from business_type string.
    Maps specific business types to one of 6 industry domains.
    
    Args:
        business_type: Specific business description (e.g., "Italian Restaurant", "Fashion Boutique")
    
    Returns:
        One of: "Restaurants", "Fashion", "E-commerce", "Tech Startup", "Healthcare", "Education"
        Defaults to "E-commerce" if no match found.
    """
    if not business_type:
        return "E-commerce"  # Default domain
    
    business_lower = business_type.lower()
    
    # Restaurants domain
    restaurant_keywords = [
        "restaurant", "cafe", "coffee", "bar", "pub", "bistro", "diner", 
        "eatery", "food", "dining", "cuisine", "kitchen", "grill", "bakery",
        "pizza", "burger", "sushi", "taco", "noodle", "ramen", "steakhouse"
    ]
    if any(keyword in business_lower for keyword in restaurant_keywords):
        return "Restaurants"
    
    # Fashion domain
    fashion_keywords = [
        "fashion", "clothing", "apparel", "boutique", "wear", "style",
        "dress", "shirt", "pants", "shoes", "accessories", "jewelry",
        "designer", "wardrobe", "outfit", "attire", "garment"
    ]
    if any(keyword in business_lower for keyword in fashion_keywords):
        return "Fashion"
    
    # Healthcare domain
    healthcare_keywords = [
        "health", "medical", "clinic", "hospital", "doctor", "dentist",
        "pharmacy", "wellness", "therapy", "care", "fitness", "gym",
        "nutrition", "mental", "physical", "rehab", "diagnostic"
    ]
    if any(keyword in business_lower for keyword in healthcare_keywords):
        return "Healthcare"
    
    # Education domain
    education_keywords = [
        "education", "school", "academy", "learning", "training", "course",
        "university", "college", "tutor", "teach", "class", "workshop",
        "institute", "coaching", "study", "academic", "student"
    ]
    if any(keyword in business_lower for keyword in education_keywords):
        return "Education"
    
    # Tech Startup domain
    tech_keywords = [
        "tech", "software", "app", "digital", "startup", "saas", "platform",
        "web", "mobile", "cloud", "ai", "data", "cyber", "it", "developer",
        "code", "programming", "automation", "api", "analytics"
    ]
    if any(keyword in business_lower for keyword in tech_keywords):
        return "Tech Startup"
    
    # Default to E-commerce for retail, shop, store, market, etc.
    return "E-commerce"


def get_industry_context(
    business_domain: str,
    business_type: Optional[str] = None,
    tone_modifier: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get industry-specific content optimization context.
    
    Args:
        business_domain: Primary business category (e.g., "Restaurants")
        business_type: Specific business type (e.g., "Italian Restaurant", "Athleisure Brand")
        tone_modifier: Sub-category tone (e.g., "fine_dining", "luxury")
    
    Returns:
        Dictionary with industry-specific hooks, CTAs, hashtags, content types
    """
    # Get base template or default to E-commerce if not found
    template = INDUSTRY_TEMPLATES.get(business_domain, INDUSTRY_TEMPLATES["E-commerce"]).copy()
    
    # Apply tone modifier if provided
    if tone_modifier and "tone_modifiers" in template:
        if tone_modifier in template["tone_modifiers"]:
            template["recommended_tone"] = template["tone_modifiers"][tone_modifier]
    
    # Add niche hashtags if business_type provided
    if business_type:
        template["hashtag_bank"]["niche"] = generate_niche_hashtags(business_type)
    
    return template


def generate_niche_hashtags(business_type: str) -> List[str]:
    """
    Generate niche-specific hashtags based on business type.
    
    Args:
        business_type: Specific business description (e.g., "Vegan Pizza Restaurant")
    
    Returns:
        List of 5-7 niche hashtags tailored to the business type
    """
    # Extract keywords from business_type
    keywords = [word for word in business_type.lower().split() if len(word) > 3]
    
    niche_tags = []
    
    for keyword in keywords:
        capitalized = keyword.capitalize()
        niche_tags.extend([
            f"#{capitalized}",
            f"#Love{capitalized}",
            f"#{capitalized}Lovers",
            f"#{capitalized}Life"
        ])
    
    # Combine keywords for compound hashtags
    if len(keywords) >= 2:
        niche_tags.append(f"#{''.join([k.capitalize() for k in keywords[:2]])}")
    
    # Remove duplicates and limit to 7
    return list(dict.fromkeys(niche_tags))[:7]


def build_industry_prompt_injection(
    business_domain: str,
    business_type: Optional[str] = None,
    tone_modifier: Optional[str] = None
) -> str:
    """
    Build prompt injection text for content generation service.
    
    Args:
        business_domain: Primary business category
        business_type: Specific business type
        tone_modifier: Sub-category tone
    
    Returns:
        Formatted string to inject into AI prompt
    """
    context = get_industry_context(business_domain, business_type, tone_modifier)
    
    prompt = f"""
## INDUSTRY-SPECIFIC OPTIMIZATION ({business_domain})

### Proven Hooks for {business_domain}:
{chr(10).join([f'- {hook}' for hook in context['hooks'][:3]])}

### High-Engagement CTAs:
{chr(10).join([f'- {cta}' for cta in context['cta_templates'][:3]])}

### Optimal Hashtag Strategy:
- Large (>1M): {', '.join(context['hashtag_bank']['large'][:3])}
- Medium (100K-1M): {', '.join(context['hashtag_bank']['medium'][:3])}
- Small (<100K): {', '.join(context['hashtag_bank']['small'][:3])}
- Niche: {', '.join(context['hashtag_bank'].get('niche', [])[:3])}

### Content Types for {business_domain}:
{chr(10).join([f'- {name}: {desc}' for name, desc in list(context['content_types'].items())[:3]])}

### Engagement Boosters:
{chr(10).join([f'- {booster}' for booster in context.get('engagement_boosters', [])[:3]])}

**IMPORTANT**: Use these industry-specific elements in your content generation.
"""
    
    return prompt


# ============================================================================
# INTEGRATION EXAMPLE
# ============================================================================

def example_usage():
    """Example of how to use industry templates in content generation"""
    
    # Example 1: Get context for a restaurant
    restaurant_context = get_industry_context(
        business_domain="Restaurants",
        business_type="Vegan Pizza Restaurant",
        tone_modifier="casual_dining"
    )
    print(f"Restaurant hooks: {restaurant_context['hooks']}")
    print(f"Niche hashtags: {restaurant_context['hashtag_bank']['niche']}")
    
    # Example 2: Build prompt injection
    prompt_injection = build_industry_prompt_injection(
        business_domain="Fashion",
        business_type="Sustainable Streetwear Brand",
        tone_modifier="streetwear"
    )
    print(prompt_injection)


if __name__ == "__main__":
    example_usage()
