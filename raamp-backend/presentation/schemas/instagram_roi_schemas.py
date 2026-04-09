from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ROIMetricsResponse(BaseModel):
    reach: int
    impressions: int
    engagement: int
    likes: int
    comments: int
    shares: int
    saved: int
    engagement_rate: float
    last_fetched_at: Optional[datetime]
    fetch_status: str

class BestPerformingPost(BaseModel):
    post_id: str
    reach: int
    engagement_rate: float

class ROISummaryResponse(BaseModel):
    total_posts: int
    total_reach: int
    prev_week_reach: int = 0
    total_impressions: int
    avg_engagement_rate: float
    best_performing_post: Optional[BestPerformingPost] = None
    worst_performing_post: Optional[BestPerformingPost] = None
    posts_pending: int
    posts_failed: int
