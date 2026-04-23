"""
Test insights with v22.0 compatible metrics
"""

import asyncio
import os
import sys

import httpx

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


async def main() -> int:
    from infrastructure.database.database import connect_to_mongo, init_db, close_mongo_connection
    from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
    from application.services.encryption_service import EncryptionService

    await connect_to_mongo()
    await init_db()
    try:
        conn = await InstagramConnectionModel.find_one(
            InstagramConnectionModel.user_id == "abdullah@gmail.com"
        )
        
        if not conn:
            print("No connection found")
            return 0
        
        token = EncryptionService().decrypt(conn.page_access_token)
        business_id = conn.ig_business_id
        
        # Get one actual media
        url = f"https://graph.facebook.com/v22.0/{business_id}/media"
        params = {
            "fields": "id",
            "access_token": token,
            "limit": 1
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params)
            media_list = r.json().get("data", [])
            
            if not media_list:
                print("No media found")
                return 0
            
            actual_media_id = media_list[0]["id"]
            print(f"Testing with actual media ID: {actual_media_id}\n")
            
            # Try the new metric list
            metrics = "reach,engagement,saved"
            insights_url = f"https://graph.facebook.com/v22.0/{actual_media_id}/insights"
            insights_params = {
                "metric": metrics,
                "access_token": token
            }
            
            print("=== Testing new metric list ===\n")
            r_insights = await client.get(insights_url, params=insights_params)
            print(f"Status: {r_insights.status_code}")
            
            insights_data = r_insights.json()
            if r_insights.status_code == 200:
                data = insights_data.get("data", [])
                print(f"Metrics received: {len(data)}")
                for metric in data:
                    name = metric.get("name")
                    values = metric.get("values", [])
                    if values:
                        value = values[0].get("value", "N/A")
                        print(f"  {name}: {value}")
            else:
                error = insights_data.get("error", {})
                print(f"Error: {error.get('message', 'Unknown')}")
                print(f"Code: {error.get('code')}")
        
        return 0
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
