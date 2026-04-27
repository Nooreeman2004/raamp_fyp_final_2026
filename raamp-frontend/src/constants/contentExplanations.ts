/**
 * Content Generation Explanations for Restaurant Owners
 * Helps non-marketers understand when to use each variant/strategy
 */

export interface VariantExplanation {
  title: string;
  description: string;
  bestFor: string;
  icon: string;
  example?: string;
}

export interface HashtagStrategyExplanation {
  title: string;
  description: string;
  purpose: string;
  icon: string;
  whenToUse: string;
}

// Caption Variant Explanations
export const CAPTION_VARIANT_EXPLANATIONS: Record<number, VariantExplanation> = {
  1: {
    title: "Short & Punchy",
    description: "Quick, attention-grabbing announcement",
    bestFor: "Instagram feed, busy scrollers, quick updates",
    icon: "⚡",
    example: "Perfect for: Daily specials, new menu items, quick announcements"
  },
  2: {
    title: "Story-Driven",
    description: "Engaging narrative that builds connection",
    bestFor: "Building relationships, storytelling, emotional connection",
    icon: "📖",
    example: "Perfect for: Behind-the-scenes, chef stories, ingredient sourcing"
  },
  3: {
    title: "Offer-Focused",
    description: "Clear promotion with strong call-to-action",
    bestFor: "Driving sales, promotions, limited-time offers",
    icon: "🎯",
    example: "Perfect for: Weekend deals, happy hour, special discounts"
  }
};

// Fallback for tones that don't match 1-3
export const getToneExplanation = (tone: string): VariantExplanation => {
  const toneLower = tone.toLowerCase();
  
  if (toneLower.includes("professional") || toneLower.includes("formal")) {
    return {
      title: "Professional",
      description: "Polished and business-appropriate",
      bestFor: "Corporate events, formal announcements",
      icon: "💼",
      example: "Perfect for: Business catering, corporate partnerships"
    };
  }
  
  if (toneLower.includes("casual") || toneLower.includes("friendly")) {
    return {
      title: "Casual & Friendly",
      description: "Warm and approachable",
      bestFor: "Daily posts, customer engagement",
      icon: "😊",
      example: "Perfect for: Regular updates, community building"
    };
  }
  
  if (toneLower.includes("urgent") || toneLower.includes("exciting")) {
    return {
      title: "Urgent & Exciting",
      description: "Creates urgency and excitement",
      bestFor: "Flash sales, limited offers",
      icon: "🔥",
      example: "Perfect for: Last-minute deals, selling out items"
    };
  }
  
  // Default fallback
  return {
    title: tone,
    description: "Custom tone variant",
    bestFor: "Various situations",
    icon: "✨",
    example: "Use based on your campaign needs"
  };
};

// Hashtag Strategy Explanations
export const HASHTAG_STRATEGY_EXPLANATIONS: Record<number, HashtagStrategyExplanation> = {
  1: {
    title: "Reach New Customers",
    description: "Discovery-focused hashtags for growth",
    purpose: "Help new people find your restaurant",
    icon: "🔍",
    whenToUse: "Use when you want to attract new customers and grow your following"
  },
  2: {
    title: "Connect with Regulars",
    description: "Community and niche-focused hashtags",
    purpose: "Build loyalty with existing customers",
    icon: "❤️",
    whenToUse: "Use when posting for your regular customers and local community"
  },
  3: {
    title: "Trending Now",
    description: "Popular and trending hashtags",
    purpose: "Ride the wave of current trends",
    icon: "📈",
    whenToUse: "Use when you want maximum visibility on trending topics"
  }
};

// Fallback for strategy names that don't match 1-3
export const getHashtagStrategyExplanation = (strategy: string): HashtagStrategyExplanation => {
  const strategyLower = strategy.toLowerCase();
  
  if (strategyLower.includes("reach") || strategyLower.includes("broad") || strategyLower.includes("discovery")) {
    return HASHTAG_STRATEGY_EXPLANATIONS[1];
  }
  
  if (strategyLower.includes("niche") || strategyLower.includes("community") || strategyLower.includes("local")) {
    return HASHTAG_STRATEGY_EXPLANATIONS[2];
  }
  
  if (strategyLower.includes("trend") || strategyLower.includes("popular") || strategyLower.includes("viral")) {
    return HASHTAG_STRATEGY_EXPLANATIONS[3];
  }
  
  if (strategyLower.includes("balanced") || strategyLower.includes("mixed")) {
    return {
      title: "Balanced Mix",
      description: "Combination of reach and niche hashtags",
      purpose: "Best of both worlds approach",
      icon: "⚖️",
      whenToUse: "Use when you want a safe, all-around strategy"
    };
  }
  
  // Default fallback
  return {
    title: strategy,
    description: "Custom hashtag strategy",
    purpose: "Tailored to your needs",
    icon: "#️⃣",
    whenToUse: "Use based on your campaign goals"
  };
};

// Helper to get explanation by variant ID
export const getVariantExplanation = (variantId: number, tone?: string): VariantExplanation => {
  // Try to get by ID first
  if (CAPTION_VARIANT_EXPLANATIONS[variantId]) {
    return CAPTION_VARIANT_EXPLANATIONS[variantId];
  }
  
  // Fallback to tone-based explanation
  if (tone) {
    return getToneExplanation(tone);
  }
  
  // Ultimate fallback
  return {
    title: "Caption Variant",
    description: "AI-generated caption",
    bestFor: "Various situations",
    icon: "✨",
    example: "Use based on your needs"
  };
};

// Helper to get hashtag explanation by set ID
export const getHashtagExplanation = (setId: number, strategy?: string): HashtagStrategyExplanation => {
  // Try to get by ID first
  if (HASHTAG_STRATEGY_EXPLANATIONS[setId]) {
    return HASHTAG_STRATEGY_EXPLANATIONS[setId];
  }
  
  // Fallback to strategy-based explanation
  if (strategy) {
    return getHashtagStrategyExplanation(strategy);
  }
  
  // Ultimate fallback
  return {
    title: "Hashtag Set",
    description: "AI-generated hashtags",
    purpose: "Increase visibility",
    icon: "#️⃣",
    whenToUse: "Use based on your campaign goals"
  };
};
