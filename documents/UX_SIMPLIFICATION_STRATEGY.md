# RAAMP UX Simplification Strategy for Restaurant Owners
**Target Audience:** Restaurant owners without marketing expertise  
**Current Suitability:** 4.5/10  
**Target Suitability:** 8.5/10  
**Date:** April 26, 2026

---

## Executive Summary

Your platform's core technology is solid, but the UX assumes marketing knowledge that restaurant owners don't have. This document provides a phased implementation plan to transform complex marketing tools into intuitive restaurant-focused workflows.

**Key Principle:** Hide complexity, surface actionable recommendations, use restaurant language.

---

## Phase 1: Quick Wins (2-3 weeks)

### 1.1 Geo-Intent: Traffic Light System

**Current Problem:** Heat scores (0-100), urgency levels, and multi-signal fusion are too technical.

**Solution:** Replace with visual traffic light system

```typescript
// Frontend: GeoIntent.tsx
interface SimplifiedOpportunity {
  level: 'great' | 'okay' | 'wait';
  icon: '🟢' | '🟡' | '🔴';
  title: string;
  action: string;
  reason: string; // Simple, one-sentence explanation
}

function simplifyHeatScore(score: number, urgency: string): SimplifiedOpportunity {
  if (score >= 70) {
    return {
      level: 'great',
      icon: '🟢',
      title: 'Great Time to Post',
      action: 'Post within the next 2 hours for best results',
      reason: 'High foot traffic and customer interest in your area right now'
    };
  } else if (score >= 40) {
    return {
      level: 'okay',
      icon: '🟡',
      title: 'Okay Time to Post',
      action: 'You can post now, but results may be average',
      reason: 'Moderate activity in your area'
    };
  } else {
    return {
      level: 'wait',
      icon: '🔴',
      title: 'Wait for Better Timing',
      action: 'Check back in a few hours',
      reason: 'Low customer activity right now'
    };
  }
}
```

**Backend Changes:** None required - this is pure frontend transformation

**Restaurant-Specific Enhancement:**
```typescript
// Add meal-time context
function addMealTimeContext(hour: number): string {
  if (hour >= 7 && hour <= 10) return 'breakfast crowd';
  if (hour >= 12 && hour <= 14) return 'lunch rush';
  if (hour >= 17 && hour <= 19) return 'happy hour';
  if (hour >= 19 && hour <= 21) return 'dinner service';
  return 'off-peak hours';
}
```

---

### 1.2 Trend Arbitrage: One-Click Content Creation

**Current Problem:** Sigma scores, market gap analysis, arbitrage potential - all financial/trading jargon.

**Solution:** Show trends as content opportunities with one button

```typescript
// Frontend: TrendArbitrage.tsx
interface SimplifiedTrend {
  topic: string;
  whyRelevant: string; // "People in Lahore are talking about Ramadan specials"
  suggestedPost: string; // Pre-generated caption
  action: 'create_post'; // Single CTA
}

// Hide all technical metrics
// Show only: trend name + why it matters + create button
```

**Backend Enhancement:**
```python
# raamp-backend/application/services/trend_detection_service.py

def generate_restaurant_angle(trend_keyword: str, business_type: str) -> str:
    """Convert trend into restaurant-specific angle"""
    
    prompt = f"""
    A {business_type} wants to create content about this trending topic: {trend_keyword}
    
    Provide:
    1. Why this trend matters for restaurants (one sentence)
    2. A ready-to-post caption (50-80 words, include 3 hashtags)
    3. Suggested dish/offer to highlight
    
    Use simple, appetizing language. No marketing jargon.
    """
    
    # Call Gemini with restaurant-specific prompt
    return llm_client.generate(prompt)
```

---

### 1.3 Campaign Planner: Template Library

**Current Problem:** Requires understanding of campaign objectives, KPIs, content pillars, budget allocation.

**Solution:** Pre-made campaign templates

```typescript
// Frontend: New component - CampaignTemplates.tsx
interface CampaignTemplate {
  id: string;
  name: string;
  icon: string;
  description: string;
  duration: string; // "3 days" not "72 hours"
  postsIncluded: number;
  autoFilled: {
    objective: string;
    timing: string[];
    contentIdeas: string[];
  };
}

const RESTAURANT_TEMPLATES: CampaignTemplate[] = [
  {
    id: 'weekend_special',
    name: 'Weekend Special Promotion',
    icon: '🍽️',
    description: 'Promote your weekend specials to nearby customers',
    duration: '3 days (Friday-Sunday)',
    postsIncluded: 3,
    autoFilled: {
      objective: 'Drive weekend foot traffic',
      timing: ['Friday 5pm', 'Saturday 12pm', 'Sunday 11am'],
      contentIdeas: [
        'Friday: Announce weekend menu',
        'Saturday: Show busy restaurant (social proof)',
        'Sunday: Last chance reminder'
      ]
    }
  },
  {
    id: 'new_menu_item',
    name: 'New Menu Item Launch',
    icon: '✨',
    description: 'Introduce a new dish to your customers',
    duration: '1 week',
    postsIncluded: 4,
    autoFilled: {
      objective: 'Build excitement for new dish',
      timing: ['Day 1: Teaser', 'Day 3: Full reveal', 'Day 5: Customer reactions', 'Day 7: Still available'],
      contentIdeas: [
        'Teaser: Behind-the-scenes prep',
        'Launch: Beautiful dish photo',
        'Social proof: Customer enjoying it',
        'Reminder: Order now'
      ]
    }
  },
  {
    id: 'slow_day_boost',
    name: 'Slow Day Traffic Boost',
    icon: '⚡',
    description: 'Fill seats on typically quiet days',
    duration: '1 day',
    postsIncluded: 2,
    autoFilled: {
      objective: 'Increase weekday lunch traffic',
      timing: ['Morning 9am', 'Lunch 11:30am'],
      contentIdeas: [
        'Morning: Lunch special announcement',
        'Midday: Limited time offer reminder'
      ]
    }
  }
];
```

**Backend Support:**
```python
# raamp-backend/application/services/campaign_template_service.py

class CampaignTemplateService:
    """Auto-fill campaign details based on template + business profile"""
    
    async def apply_template(
        self,
        template_id: str,
        business_id: str
    ) -> dict:
        """
        Takes a template and business context,
        returns a fully-configured campaign ready to launch
        """
        business = await self.business_repo.get_by_id(business_id)
        template = TEMPLATES[template_id]
        
        # Auto-generate captions for each post in template
        captions = []
        for content_idea in template['contentIdeas']:
            caption = await self.content_service.generate_content(
                campaign_idea=content_idea,
                business_name=business.name,
                tone="friendly and appetizing"
            )
            captions.append(caption)
        
        return {
            "template_name": template['name'],
            "posts": [
                {
                    "scheduled_time": time,
                    "caption": caption,
                    "content_idea": idea
                }
                for time, caption, idea in zip(
                    template['timing'],
                    captions,
                    template['contentIdeas']
                )
            ],
            "ready_to_launch": True
        }
```

---

## Phase 2: Core Module Redesigns (4-6 weeks)

### 2.1 Dashboard: Contextual Metrics

**Current Problem:** Too many metrics without context. Restaurant owners don't understand "impressions" vs "reach" vs "engagement".

**Solution:** Add tooltips and benchmarks in restaurant terms

```typescript
// Frontend: Dashboard.tsx
interface MetricWithContext {
  value: number;
  label: string;
  tooltip: string; // Plain English explanation
  benchmark?: string; // "Good for a restaurant your size"
  trend: 'up' | 'down' | 'stable';
}

const METRIC_EXPLANATIONS = {
  reach: {
    tooltip: "How many people saw your posts. Like counting people who walked past your restaurant window.",
    goodBenchmark: (value: number, avgSeats: number) => {
      const ratio = value / avgSeats;
      if (ratio > 50) return "Excellent - you're reaching 50x your seating capacity";
      if (ratio > 20) return "Good - you're reaching 20x your seating capacity";
      return "Room to grow - try posting at peak meal times";
    }
  },
  engagement: {
    tooltip: "How many people liked, commented, or shared. Like customers who stopped to read your menu board.",
    goodBenchmark: (engagementRate: number) => {
      if (engagementRate > 5) return "Excellent - people love your content";
      if (engagementRate > 2) return "Good - your posts are interesting";
      return "Try posting mouth-watering food photos";
    }
  },
  impressions: {
    tooltip: "Total times your posts were shown (includes people seeing them multiple times).",
    goodBenchmark: () => "This number is usually 2-3x your reach"
  }
};
```

---

### 2.2 Geo-Intent: Deploy Package Export (Already Implemented)

**Current Status:** ✅ Already simplified in latest code

The platform already exports a campaign package instead of trying to auto-deploy:
- Copy-ready caption (no technical formatting)
- Targeting parameters (area name or coordinates + radius)
- Persona split (when valid)

**Enhancement:** Add visual guide

```typescript
// Frontend: Add step-by-step guide modal
const MetaAdsGuide = () => (
  <Dialog>
    <DialogContent>
      <h2>How to Use Your Campaign Package</h2>
      <ol className="space-y-4">
        <li>
          <strong>Step 1:</strong> Copy the caption below
          <Button>Copy Caption</Button>
        </li>
        <li>
          <strong>Step 2:</strong> Open Facebook Ads Manager
          <Button onClick={() => window.open('https://adsmanager.facebook.com')}>
            Open Ads Manager
          </Button>
        </li>
        <li>
          <strong>Step 3:</strong> Create new campaign, paste caption
        </li>
        <li>
          <strong>Step 4:</strong> Set location to: <code>{areaName}</code>
        </li>
        <li>
          <strong>Step 5:</strong> Set radius to: <code>{radiusKm} km</code>
        </li>
      </ol>
      <video src="/tutorials/meta-ads-setup.mp4" controls />
    </DialogContent>
  </Dialog>
);
```

---

### 2.3 Content Generation: Guided Wizard

**Current Problem:** Users face blank "campaign idea" field with no guidance.

**Solution:** Add campaign idea templates and prompts

```typescript
// Frontend: CreativeStudio.tsx enhancement
const CAMPAIGN_IDEA_TEMPLATES = [
  {
    category: 'Daily Specials',
    ideas: [
      'Lunch special: Biryani + drink for Rs. 350',
      'Happy hour: Buy 1 get 1 on appetizers',
      'Chef\'s special: New pasta dish this week'
    ]
  },
  {
    category: 'Events & Occasions',
    ideas: [
      'Ramadan Iftar buffet booking now open',
      'Valentine\'s Day couple dinner package',
      'Birthday party packages available'
    ]
  },
  {
    category: 'Customer Engagement',
    ideas: [
      'Share your favorite dish and get featured',
      'Tag us in your food photos for a chance to win',
      'Customer appreciation week - thank you for 5 years'
    ]
  },
  {
    category: 'Seasonal',
    ideas: [
      'Beat the heat with our new cold beverages',
      'Cozy winter soups now available',
      'Mango season specials'
    ]
  }
];

// Show template picker before free-form input
<Select onValueChange={(template) => setCampaignIdea(template)}>
  <SelectTrigger>
    <SelectValue placeholder="Choose a campaign idea or write your own" />
  </SelectTrigger>
  <SelectContent>
    {CAMPAIGN_IDEA_TEMPLATES.map(category => (
      <SelectGroup key={category.category}>
        <SelectLabel>{category.category}</SelectLabel>
        {category.ideas.map(idea => (
          <SelectItem value={idea}>{idea}</SelectItem>
        ))}
      </SelectGroup>
    ))}
  </SelectContent>
</Select>
```

---

## Phase 3: Advanced Simplifications (6-8 weeks)

### 3.1 Unified "Post Now" Workflow

**Goal:** One button that does everything

```typescript
// Frontend: New component - QuickPostWizard.tsx
interface QuickPostStep {
  id: string;
  question: string;
  options: string[];
  autoDetect?: () => Promise<string>; // AI suggestion
}

const QUICK_POST_WIZARD: QuickPostStep[] = [
  {
    id: 'timing',
    question: 'When do you want to post?',
    options: ['Right now', 'Best time today', 'Schedule for later'],
    autoDetect: async () => {
      // Call Geo-Intent to check if now is good
      const opportunity = await geoIntentService.checkOpportunity();
      return opportunity.level === 'great' ? 'Right now' : 'Best time today';
    }
  },
  {
    id: 'content_type',
    question: 'What are you promoting?',
    options: [
      'Daily special',
      'New menu item',
      'Event/occasion',
      'General update',
      'Customer appreciation'
    ]
  },
  {
    id: 'auto_generate',
    question: 'We can write the post for you',
    options: ['Yes, write it for me', 'I\'ll write my own']
  }
];

// Behind the scenes, this wizard:
// 1. Checks Geo-Intent for timing
// 2. Checks Trends for relevant topics
// 3. Generates caption via Content Generation
// 4. Schedules via Smart Scheduling
// All without user seeing the complexity
```

---

### 3.2 Restaurant-Specific Onboarding

**Enhancement:** Tailor onboarding questions to restaurant context

```typescript
// Backend: Update onboarding flow
interface RestaurantOnboarding {
  // Instead of "business specialties" (marketing term)
  cuisine_type: string[]; // "Pakistani", "Fast Food", "Fine Dining"
  signature_dishes: string[]; // "Biryani", "Karahi", "BBQ"
  meal_services: string[]; // "Breakfast", "Lunch", "Dinner", "Late Night"
  dining_options: string[]; // "Dine-in", "Takeout", "Delivery", "Catering"
  
  // Instead of "target audience" (marketing term)
  typical_customers: string[]; // "Families", "Students", "Office workers", "Couples"
  
  // Instead of "brand tone" (marketing term)
  restaurant_vibe: string; // "Casual and friendly", "Upscale and elegant", "Fast and convenient"
}
```

---

### 3.3 Performance Prediction: Simple Language

**Current Problem:** "ML score", "predicted performance" are abstract.

**Solution:** Use outcome-focused language

```typescript
// Frontend: Caption variant display
interface SimplifiedPrediction {
  caption: string;
  expectedOutcome: string; // Plain English
  confidence: 'high' | 'medium' | 'low';
}

function translateMLScore(mlScore: number): SimplifiedPrediction {
  if (mlScore > 0.7) {
    return {
      expectedOutcome: 'This caption will likely get lots of likes and comments',
      confidence: 'high'
    };
  } else if (mlScore > 0.4) {
    return {
      expectedOutcome: 'This caption should perform okay',
      confidence: 'medium'
    };
  } else {
    return {
      expectedOutcome: 'This caption might not get much engagement',
      confidence: 'low'
    };
  }
}
```

---

## Phase 4: Terminology Overhaul (Ongoing)

### 4.1 Marketing Terms → Restaurant Terms

| Current (Marketing) | New (Restaurant) |
|---------------------|------------------|
| Campaign | Promotion |
| Content Generation | Write My Post |
| Geo-Intent Heat Score | Customer Activity Level |
| Trend Arbitrage | What's Trending |
| Campaign Planner | Promotion Calendar |
| Target Audience | My Customers |
| Brand Voice | Restaurant Style |
| Engagement Rate | Customer Interest |
| Impressions | Times Seen |
| Reach | People Reached |
| KPIs | Results |
| ROI | Money Made vs Money Spent |
| CTA | Call to Action → "What you want customers to do" |
| Hashtags | Search Tags |
| Caption | Post Text |

### 4.2 Implementation

```typescript
// Create terminology mapping file
// raamp-frontend/src/constants/terminology.ts

export const TERMINOLOGY = {
  campaign: {
    marketing: 'Campaign',
    restaurant: 'Promotion',
    tooltip: 'A series of posts to promote something specific'
  },
  engagement_rate: {
    marketing: 'Engagement Rate',
    restaurant: 'Customer Interest',
    tooltip: 'Percentage of people who liked, commented, or shared your post'
  },
  // ... etc
};

// Use throughout app
import { TERMINOLOGY } from '@/constants/terminology';

<Label>{TERMINOLOGY.campaign.restaurant}</Label>
```

---

## Implementation Priority Matrix

### Must Have (Phase 1 - Weeks 1-3)
1. ✅ Geo-Intent traffic light system
2. ✅ Campaign templates library
3. ✅ Content generation idea templates
4. ✅ Dashboard metric tooltips

### Should Have (Phase 2 - Weeks 4-6)
5. ✅ Trend one-click content creation
6. ✅ Terminology overhaul
7. ✅ Restaurant-specific onboarding
8. ✅ Meta Ads visual guide

### Nice to Have (Phase 3 - Weeks 7-8)
9. ⏳ Unified "Post Now" wizard
10. ⏳ Performance prediction in plain English
11. ⏳ Video tutorials for each feature

---

## Success Metrics

Track these to measure if simplification is working:

1. **Completion Rate:** % of users who complete their first post (target: 80%+)
2. **Time to First Post:** Average time from signup to first post (target: <10 minutes)
3. **Feature Adoption:** % of users who use Geo-Intent, Trends, etc. (target: 60%+)
4. **Support Tickets:** Reduction in "how do I..." questions (target: -50%)
5. **User Satisfaction:** NPS score from restaurant owners (target: 50+)

---

## Next Steps

1. **Week 1:** Implement Geo-Intent traffic light system (frontend only, no backend changes)
2. **Week 2:** Create campaign template library + backend auto-fill service
3. **Week 3:** Add content generation idea templates
4. **Week 4:** Begin terminology overhaul across all pages
5. **Week 5-6:** Restaurant-specific onboarding flow
6. **Week 7-8:** Unified "Post Now" wizard

---

## Technical Notes

### No Breaking Changes Required

All simplifications can be implemented as:
- **Frontend transformations** of existing API responses
- **Additive backend endpoints** (templates, suggestions)
- **UI layer changes** (terminology, tooltips, wizards)

Existing APIs remain unchanged, ensuring backward compatibility.

### Restaurant-Specific AI Prompts

Update all Gemini prompts to include restaurant context:

```python
# Add to all content generation prompts
RESTAURANT_CONTEXT = """
You are writing for a restaurant owner who wants to attract more customers.
Use simple, appetizing language. Focus on food, atmosphere, and customer experience.
Avoid marketing jargon. Write like you're talking to a friend about a great meal.
"""
```

---

**Document Status:** Draft v1.0  
**Last Updated:** April 26, 2026  
**Owner:** Product Team  
**Reviewers:** Engineering, UX, Restaurant Owner Focus Group
