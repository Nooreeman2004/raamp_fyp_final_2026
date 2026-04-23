"""
application/services/comment_analysis_service.py
Fetches comments for a post and runs spam + sentiment analysis on each.
"""

import logging
from ml.comment_analyser import analyse_comment
from application.services.instagram_graph_api_service import fetch_comments

logger = logging.getLogger(__name__)


async def analyse_post_comments(post_id: str) -> dict:
    """
    Fetch all comments for a post and analyse each one.
    Results are cached in the database (CommentAnalysisModel).
    Returns a summary + per-comment breakdown.
    """
    from infrastructure.database.models.comment_analysis_model import CommentAnalysisModel
    from datetime import datetime

    # 1. Fetch raw comments from Instagram
    raw_comments = await fetch_comments(post_id)

    if not raw_comments:
        return {
            "post_id": post_id,
            "total": 0,
            "spam_count": 0,
            "sentiment_summary": {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0},
            "comments": []
        }

    # 2. Analyse each comment (with DB caching)
    analysed = []
    for comment in raw_comments:
        comment_id = str(comment.get("id"))
        text = comment.get("text", "")
        if not text:
            continue

        # Check DB for existing analysis
        existing = await CommentAnalysisModel.find_one(CommentAnalysisModel.comment_id == comment_id)
        
        if existing and existing.text == text:
            # Use cached result
            analysis_result = {
                "is_spam": existing.is_spam,
                "spam_confidence": existing.spam_confidence,
                "sentiment": existing.sentiment,
                "sentiment_score": existing.sentiment_score
            }
        else:
            # Run fresh analysis
            analysis_result = analyse_comment(text)
            
            # Save/Update in DB
            if existing:
                existing.text = text
                existing.is_spam = analysis_result["is_spam"]
                existing.spam_confidence = analysis_result["spam_confidence"]
                existing.sentiment = analysis_result["sentiment"]
                existing.sentiment_score = analysis_result["sentiment_score"]
                existing.analyzed_at = datetime.utcnow()
                await existing.save()
            else:
                await CommentAnalysisModel(
                    comment_id=comment_id,
                    post_id=post_id,
                    text=text,
                    is_spam=analysis_result["is_spam"],
                    spam_confidence=analysis_result["spam_confidence"],
                    sentiment=analysis_result["sentiment"],
                    sentiment_score=analysis_result["sentiment_score"]
                ).insert()

        analysed.append({
            "id":               comment_id,
            "text":             text,
            "timestamp":        comment.get("timestamp"),
            "is_spam":          analysis_result["is_spam"],
            "spam_confidence":  analysis_result["spam_confidence"],
            "sentiment":        analysis_result["sentiment"],
            "sentiment_score":  analysis_result["sentiment_score"],
        })

    # 3. Build summary
    spam_count = sum(1 for c in analysed if c["is_spam"])

    sentiment_summary = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
    for c in analysed:
        if not c["is_spam"]:  # only count non-spam in sentiment
            sentiment_summary[c["sentiment"]] += 1

    return {
        "post_id":          post_id,
        "total":            len(analysed),
        "spam_count":       spam_count,
        "sentiment_summary": sentiment_summary,
        "comments":         analysed
    }