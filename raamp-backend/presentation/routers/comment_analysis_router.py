"""
presentation/routers/comment_analysis_router.py — Comment Intelligence API
========================================================================
Exposes endpoints for bulk comment analysis (per post) and single-comment
real-time analysis for the frontend.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from presentation.routers.auth_router import get_current_user_email
from application.constants import PaginationDefaults
from application.utils.tier_restrictions import require_pro_or_premium
from infrastructure.database.models.user_model import UserModel
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
    user: UserModel = Depends(require_pro_or_premium),  # Pro/Premium only
    sentiment: Optional[str] = Query(None, description="Filter by sentiment: POSITIVE, NEUTRAL, NEGATIVE"),
    limit: int = Query(PaginationDefaults.DEFAULT_LIMIT_COMMENTS, le=PaginationDefaults.MAX_LIMIT_COMMENTS, description="Max comments to return")
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
    user: UserModel = Depends(require_pro_or_premium),  # Pro/Premium only
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
    user: UserModel = Depends(require_pro_or_premium),  # Pro/Premium only
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

@router.delete("/bulk-delete", summary="Bulk delete comments from platform and database")
async def bulk_delete_comments(
    payload: dict,
    current_user_email: str = Depends(get_current_user_email),
    user: UserModel = Depends(require_pro_or_premium),
):
    """
    Deletes multiple comments from both the social platform (Meta) and our analysis database.
    """
    from infrastructure.database.models.comment_analysis_model import CommentAnalysisModel
    from infrastructure.database.models.auto_reply_models import CommentEventModel
    from application.services.instagram_graph_api_service import InstagramGraphAPIClient
    from application.services.facebook_graph_api_service import FacebookGraphAPIClient
    from infrastructure.database.models.facebook_connection_model import FacebookConnectionModel

    comment_ids = payload.get("comment_ids", [])
    if not comment_ids:
        return {"success": True, "deleted_count": 0}

    logger.info("🗑️ Bulk delete request for %d comments from %s", len(comment_ids), current_user_email)
    
    deleted_count = 0
    errors = []

    ig_client = InstagramGraphAPIClient()
    
    for cid in comment_ids:
        try:
            # 1. Find the platform context from CommentEventModel
            event = await CommentEventModel.find_one(CommentEventModel.comment_id == cid)
            if not event:
                # If no event, we can only delete from our analysis DB
                logger.warning("⚠️ No CommentEvent found for %s, deleting from local DB only", cid)
            else:
                # 2. Delete from platform
                try:
                    if event.platform == "instagram":
                        await ig_client.delete_comment(current_user_email, cid)
                    elif event.platform == "facebook":
                        # For FB, we need the page access token
                        fb_conn = await FacebookConnectionModel.find_one(FacebookConnectionModel.user_id == current_user_email)
                        if fb_conn and event.page_id:
                            async with FacebookGraphAPIClient() as fb_client:
                                page_token = await fb_client.get_page_access_token(fb_conn.access_token, str(event.page_id))
                                await fb_client.delete_comment(comment_id=cid, page_access_token=page_token)
                except Exception as meta_err:
                    logger.error("❌ Meta deletion failed for %s: %s", cid, meta_err)
                    # We continue to delete from our DB even if Meta fails (maybe it was already deleted there)

            # 3. Delete from CommentAnalysisModel
            analysis = await CommentAnalysisModel.find_one(CommentAnalysisModel.comment_id == cid)
            if analysis:
                await analysis.delete()
                deleted_count += 1
                
        except Exception as e:
            logger.error("❌ Failed to process deletion for %s: %s", cid, e)
            errors.append(str(e))

    return {
        "success": True, 
        "deleted_count": deleted_count,
        "errors": errors if errors else None
    }

@router.post("/{comment_id}/mark-valid", summary="Mark a comment as legitimate (not spam)")
async def mark_comment_as_valid(
    comment_id: str,
    current_user_email: str = Depends(get_current_user_email),
    user: UserModel = Depends(require_pro_or_premium),
):
    """
    Clears the spam flag for a comment in our database.
    """
    from infrastructure.database.models.comment_analysis_model import CommentAnalysisModel
    
    analysis = await CommentAnalysisModel.find_one(CommentAnalysisModel.comment_id == comment_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Comment analysis not found")
    
    analysis.is_spam = False
    analysis.spam_confidence = 0.0  # Reset confidence
    await analysis.save()
    
    return {"success": True, "message": "Comment marked as legitimate"}
