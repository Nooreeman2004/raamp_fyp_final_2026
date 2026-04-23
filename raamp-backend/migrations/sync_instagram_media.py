"""
Sync actual Instagram media into database.
This resolves the issue where stored media IDs don't match actual Instagram posts.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

import httpx

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


async def main() -> int:
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
    from infrastructure.database.models.instagram_post_model import (
        InstagramPostModel,
        ROIMetrics
    )
    from application.services.encryption_service import EncryptionService

    await connect_to_mongo()
    await init_db()
    try:
        # Get all connections
        connections = await InstagramConnectionModel.find_all().to_list()
        
        enc = EncryptionService()
        total_synced = 0
        
        for conn in connections:
            if not conn.page_access_token:
                continue
            
            token = enc.decrypt(conn.page_access_token)
            business_id = conn.ig_business_id
            user_id = conn.user_id
            
            print(f"\nSyncing media for user: {user_id}, business: {business_id}")
            
            # Fetch actual media from Instagram
            url = f"https://graph.facebook.com/v22.0/{business_id}/media"
            params = {
                "fields": "id,media_type,media_product_type,caption,created_time,permalink",
                "access_token": token,
                "limit": 100
            }
            
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    r = await client.get(url, params=params)
                    
                    if r.status_code != 200:
                        print(f"  Error fetching media: {r.status_code}")
                        continue
                    
                    media_list = r.json().get("data", [])
                    print(f"  Found {len(media_list)} media items on Instagram")
                    
                    # Fetch insights for each media
                    for media in media_list:
                        media_id = media["id"]
                        media_type = media.get("media_type", "UNKNOWN")
                        
                        # Check if this media already exists in DB
                        existing = await InstagramPostModel.find_one(
                            InstagramPostModel.instagram_post_id == media_id
                        )
                        
                        if existing:
                            # Already in DB, skip
                            continue
                        
                        # Fetch insights for this media
                        insights_url = f"https://graph.facebook.com/v22.0/{media_id}/insights"
                        insights_params = {
                            "metric": "reach,impressions,likes,comments,shares,saved,total_interactions",
                            "access_token": token
                        }
                        
                        try:
                            insights_res = await client.get(insights_url, params=insights_params)
                            
                            if insights_res.status_code == 200:
                                insights_data = insights_res.json().get("data", [])
                                metrics_map = {
                                    m["name"]: m["values"][0]["value"]
                                    for m in insights_data if m.get("values")
                                }
                                
                                # Create new post record
                                new_post = InstagramPostModel(
                                    user_id=user_id,
                                    ig_business_id=business_id,
                                    media_url=media.get("permalink", ""),
                                    caption=media.get("caption", ""),
                                    media_type=media_type,
                                    status="published",
                                    instagram_post_id=media_id,
                                    published_at=datetime.now(timezone.utc),
                                    roi_metrics=ROIMetrics(
                                        reach=metrics_map.get("reach", 0),
                                        impressions=metrics_map.get("impressions", 0),
                                        engagement=metrics_map.get("total_interactions", 0),
                                        likes=metrics_map.get("likes", 0),
                                        comments=metrics_map.get("comments", 0),
                                        shares=metrics_map.get("shares", 0),
                                        saved=metrics_map.get("saved", 0),
                                        engagement_rate=0.0,  # Will be calculated above
                                        fetch_status="success",
                                        last_fetched_at=datetime.now(timezone.utc)
                                    )
                                )
                                
                                # Calculate engagement rate
                                reach = metrics_map.get("reach", 0)
                                if reach > 0:
                                    total_eng = metrics_map.get("total_interactions", 0) or (
                                        metrics_map.get("likes", 0) + 
                                        metrics_map.get("comments", 0) + 
                                        metrics_map.get("shares", 0)
                                    )
                                    new_post.roi_metrics.engagement_rate = round((total_eng / reach) * 100, 2)
                                
                                await new_post.insert()
                                total_synced += 1
                                print(f"    ✓ Synced: {media_id} (reach: {new_post.roi_metrics.reach})")
                            else:
                                print(f"    ✗ Failed to get insights for {media_id}")
                        
                        except Exception as e:
                            print(f"    ✗ Error processing media {media_id}: {str(e)[:80]}")
            
            except Exception as e:
                print(f"  Error syncing media: {str(e)[:100]}")
        
        print(f"\n=== Sync Complete ===")
        print(f"Total media items synced: {total_synced}")
        return 0
    
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
