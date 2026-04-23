"""
presentation/routers/comment_analysis_router.py — Comment Intelligence API
========================================================================
Exposes endpoints for bulk comment analysis (per post) and single-comment
real-time analysis for the frontend.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from presentation.routers.auth_router import get_current_user_email
from typing import Optional
from pymongo import DESCENDING

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/comments", tags=["ML — Comment Analysis"])

# Startup verification log
logger.info("🔧 Comment Analysis Router initialized with prefix: /api/comments")

@router.get("/test-moderation-simple", summary="TEST - Simple moderation endpoint without auth")
async def test_moderation_simple():
    """Test endpoint to verify routing works"""
    return {"success": True, "message": "Moderation router is working!", "data": {"total": 0, "comments": []}}

@router.get("/moderation", summary="Get all analyzed comments for moderation dashboard")
async def get_moderation_comments(
    _current_user: str = Depends(get_current_user_email),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment: POSITIVE, NEUTRAL, NEGATIVE"),
    limit: int = Query(100, le=500, description="Max comments to return")
):
    """
    Fetch all analyzed comments from the database for the Social Moderation dashboard.
    Returns ALL comments with their spam scores - UI handles display filtering.
    """
    logger.info("📥 GET /api/comments/moderation - sentiment=%s, limit=%d", sentiment, limit)
    from infrastructure.database.models.comment_analysis_model import CommentAnalysisModel
    
    try:
        # Build query - only filter by sentiment if specified
        query_filters = []
        
        if sentiment and sentiment in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
            query_filters.append(CommentAnalysisModel.sentiment == sentiment)
        
        # Fetch comments with descending sort on analyzed_at
        if query_filters:
            comments = await CommentAnalysisModel.find(
                *query_filters
            ).sort([("analyzed_at", DESCENDING)]).limit(limit).to_list()
        else:
            comments = await CommentAnalysisModel.find_all().sort(
                [("analyzed_at", DESCENDING)]
            ).limit(limit).to_list()
        
        # Calculate summary statistics
        total_count = len(comments)
        spam_count = sum(1 for c in comments if c.is_spam)
        sentiment_summary = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
        
        for comment in comments:
            if comment.sentiment in sentiment_summary:
                sentiment_summary[comment.sentiment] += 1
        
        # Format response
        formatted_comments = [
            {
                "id": str(c.id),
                "comment_id": c.comment_id,
                "post_id": c.post_id,
                "text": c.text,
                "is_spam": c.is_spam,
                "spam_confidence": c.spam_confidence,
                "sentiment": c.sentiment,
                "sentiment_score": c.sentiment_score,
                "analyzed_at": c.analyzed_at.isoformat() if c.analyzed_at else None
            }
            for c in comments
        ]
        
        logger.info(
            "✅ Moderation comments fetched: total=%d, spam=%d, sentiments=%s",
            total_count, spam_count, sentiment_summary
        )
        
        return {
            "success": True,
            "data": {
                "total": total_count,
                "spam_count": spam_count,
                "sentiment_summary": sentiment_summary,
                "comments": formatted_comments
            }
        }
    except Exception as exc:
        logger.exception("❌ Error fetching moderation comments: %s", str(exc))
        raise HTTPException(status_code=500, detail=f"Failed to fetch comments: {str(exc)}") from exc

@router.get("/summary/{post_id}", summary="Get spam + sentiment analysis for a post's comments")
async def get_comment_summary(
    post_id: str,
    _current_user: str = Depends(get_current_user_email),
):
    """
    Fetch all comments for a specific post and perform bulk sentiment/spam analysis.
    Useful for populating the intelligence grid on the Campaign Planner Detail view.
    """
    from application.services.comment_analysis_service import analyse_post_comments
    try:
        # Note: analyse_post_comments is async and must be awaited
        result = await analyse_post_comments(post_id)
        return {"success": True, "data": result}
    except Exception as exc:
        logger.error("Comment analysis failed for post %s: %s", post_id, exc)
        raise HTTPException(status_code=500, detail=f"Comment analysis failed: {str(exc)}") from exc

@router.post("/analyse", summary="Analyse a single comment for spam and sentiment")
async def analyse_single_comment(
    payload: dict,
    _current_user: str = Depends(get_current_user_email),
):
    """
    Real-time analysis for a single piece of text.
    Used by the frontend to preview sentiment before posting or for manual checks.
    """
    from ml.comment_analyser import analyse_comment
    try:
        text = payload.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        # This call handles its own model loading/lazy initialization
        result = analyse_comment(text)
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Single comment analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(exc)}") from exc
