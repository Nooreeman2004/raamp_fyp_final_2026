"""
Backfill historical Instagram comments into the comment analysis system.
Fetches comments from existing Instagram posts and analyzes them for spam/sentiment.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.instagram_post_model import InstagramPostModel
    from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
    from infrastructure.database.models.comment_analysis_model import CommentAnalysisModel
    from application.services.encryption_service import EncryptionService
    from ml.comment_analyser import analyse_comment
    import httpx

    print("=" * 80)
    print("BACKFILL HISTORICAL INSTAGRAM COMMENTS")
    print("=" * 80)

    await connect_to_mongo()
    await init_db()

    try:
        enc = EncryptionService()
        
        # Get all Instagram connections
        connections = await InstagramConnectionModel.find_all().to_list()
        
        if not connections:
            print("❌ No Instagram connections found")
            return 1
        
        print(f"\n✅ Found {len(connections)} Instagram connection(s)")
        
        total_analyzed = 0
        
        for conn in connections:
            if not conn.page_access_token or not conn.ig_business_id:
                continue
            
            user_id = conn.user_id
            ig_business_id = conn.ig_business_id
            token = enc.decrypt(conn.page_access_token)
            
            print(f"\n{'='*80}")
            print(f"Processing user: {user_id}")
            print(f"Instagram Business ID: {ig_business_id}")
            print(f"{'='*80}")
            
            # Get user's Instagram posts from database
            posts = await InstagramPostModel.find(
                InstagramPostModel.ig_business_id == ig_business_id
            ).to_list()
            
            print(f"\n📊 Found {len(posts)} posts in database")
            
            if not posts:
                print("   No posts to process")
                continue
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for idx, post in enumerate(posts, 1):
                    post_id = post.instagram_post_id
                    print(f"\n[{idx}/{len(posts)}] Processing post: {post_id}")
                    
                    try:
                        # Fetch comments from Instagram Graph API
                        comments_url = f"https://graph.facebook.com/v22.0/{post_id}/comments"
                        params = {
                            "access_token": token,
                            "fields": "id,text,timestamp,from",
                            "limit": 100  # Fetch up to 100 comments per post
                        }
                        
                        response = await client.get(comments_url, params=params)
                        
                        if response.status_code != 200:
                            print(f"   ⚠️  Failed to fetch comments: {response.status_code}")
                            print(f"       Response: {response.text[:200]}")
                            continue
                        
                        data = response.json()
                        comments = data.get("data", [])
                        
                        if not comments:
                            print(f"   📭 No comments found")
                            continue
                        
                        print(f"   💬 Found {len(comments)} comment(s)")
                        
                        # Analyze each comment
                        for comment in comments:
                            comment_id = comment.get("id")
                            text = comment.get("text", "")
                            timestamp = comment.get("timestamp")
                            
                            if not text or not comment_id:
                                continue
                            
                            # Check if already analyzed
                            existing = await CommentAnalysisModel.find_one(
                                CommentAnalysisModel.comment_id == comment_id
                            )
                            
                            if existing:
                                print(f"      ✓ Already analyzed: {comment_id[:20]}...")
                                continue
                            
                            # Analyze comment with ML model
                            try:
                                analysis = analyse_comment(text)
                                
                                # Parse timestamp
                                analyzed_at = None
                                if timestamp:
                                    try:
                                        analyzed_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                    except:
                                        analyzed_at = datetime.utcnow()
                                else:
                                    analyzed_at = datetime.utcnow()
                                
                                # Store analysis
                                comment_analysis = CommentAnalysisModel(
                                    comment_id=comment_id,
                                    post_id=post_id,
                                    text=text,
                                    is_spam=analysis["is_spam"],
                                    spam_confidence=analysis["spam_confidence"],
                                    sentiment=analysis["sentiment"],
                                    sentiment_score=analysis["sentiment_score"],
                                    analyzed_at=analyzed_at
                                )
                                
                                await comment_analysis.insert()
                                
                                spam_label = "🚫 SPAM" if analysis["is_spam"] else "✅ OK"
                                sentiment_emoji = {
                                    "POSITIVE": "😊",
                                    "NEUTRAL": "😐",
                                    "NEGATIVE": "😞"
                                }.get(analysis["sentiment"], "")
                                
                                print(f"      ✅ {spam_label} {sentiment_emoji} {analysis['sentiment']} | {text[:50]}...")
                                total_analyzed += 1
                                
                            except Exception as e:
                                print(f"      ❌ Analysis failed: {str(e)[:100]}")
                                continue
                        
                        # Small delay between posts to avoid rate limits
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        print(f"   ❌ Error processing post: {str(e)[:200]}")
                        continue
        
        print(f"\n{'='*80}")
        print(f"✅ BACKFILL COMPLETE")
        print(f"   Total comments analyzed: {total_analyzed}")
        print(f"{'='*80}\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
