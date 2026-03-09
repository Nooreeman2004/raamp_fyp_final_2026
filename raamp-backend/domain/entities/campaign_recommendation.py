
# Domain Layer - Campaign Recommendation Entity
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class CampaignRecommendation:
    """Represents an AI-generated marketing campaign recommendation based on trend data"""
    trend_name: str
    campaign_idea: str
    recommended_platform: str
    reasoning: str
    expected_marketing_goal: str
    suggested_hooks: List[str]
    estimated_effort: str # Low, Medium, High
    priority: int # 1-10
