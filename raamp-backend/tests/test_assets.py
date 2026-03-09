import asyncio
from infrastructure.database.database import connect_to_mongo, init_db
from infrastructure.repositories.asset_repository import AssetRepository

async def test_library():
    await connect_to_mongo()
    await init_db()
    
    repo = AssetRepository()
    
    try:
        # Fetch all assets
        from infrastructure.database.models.asset_model import AssetModel
        assets = await AssetModel.find_all().to_list()
        print(f"Fetched {len(assets)} assets total in DB")
        
        # Test the router conversion logic
        from presentation.routers.assets_router import AssetResponse
        
        for asset in assets:
            try:
                response = AssetResponse(
                    asset_id=asset.asset_id,
                    storage_url=asset.storage_url,
                    cloudinary_url=asset.cloudinary_url,
                    firebase_url=asset.firebase_url,
                    file_name=asset.file_name,
                    file_size_bytes=asset.file_size_bytes,
                    content_type=asset.content_type,
                    width=asset.width,
                    height=asset.height,
                    asset_type=asset.asset_type.value,
                    generation_source=asset.generation_source.value,
                    generation_prompt=asset.generation_prompt,
                    campaign_idea=asset.campaign_idea,
                    variation_number=asset.variation_number,
                    model_used=asset.model_used,
                    times_used=asset.times_used,
                    last_used_at=asset.last_used_at.isoformat() if asset.last_used_at else None,
                    tags=asset.tags,
                    is_favorite=asset.is_favorite,
                    created_at=asset.created_at.isoformat(),
                    updated_at=asset.updated_at.isoformat()
                )
                print(f"Successfully converted asset {asset.asset_id}")
            except Exception as e:
                print(f"FAILED to convert asset {asset.asset_id}: {repr(e)}")
                print(f"Asset dict: {asset.model_dump()}")
                
        # TEST CAPTIONS LOGIC
        from infrastructure.repositories.caption_log_repository import CaptionLogRepository
        caption_repo = CaptionLogRepository()
        captions = await caption_repo.get_by_user_id(user_id="test@example.com", limit=50) # doesn't matter, just to see what happens
        from infrastructure.database.models.caption_log_model import CaptionLogModel
        captions = await CaptionLogModel.find_all().to_list()
        print(f"Fetched {len(captions)} captions total in DB")
        
        from presentation.routers.assets_router import CaptionAsset
        for caption in captions:
            try:
                # Same conversion as in assets_router.py
                CaptionAsset(
                    caption_id=caption.caption_id,
                    caption_text=caption.caption_text,
                    hashtags=caption.hashtags,
                    tone=caption.tone,
                    asset_type=caption.asset_type.value if hasattr(caption.asset_type, 'value') else caption.asset_type,
                    platform=caption.asset_type.value if hasattr(caption.asset_type, 'value') else caption.asset_type,
                    created_at=caption.created_at.isoformat(),
                    campaign_id=caption.campaign_id,
                    campaign_idea=caption.campaign_idea,
                    times_used=caption.times_used,
                    is_favorite=caption.is_favorite,
                    predicted_performance=caption.predicted_performance
                )
                print(f"Successfully converted caption {caption.caption_id}")
            except Exception as e:
                print(f"FAILED to convert caption {caption.caption_id}: {repr(e)}")
                
    except Exception as e:
        print(f"FAILED to fetch assets: {repr(e)}")

if __name__ == "__main__":
    asyncio.run(test_library())
