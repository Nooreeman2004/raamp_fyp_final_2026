"""
📊 Check Asset File Paths
=========================
Verify that asset file paths in the database exist on disk.
Useful for debugging 404 errors in A/B optimizer.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.repositories.asset_repository import AssetRepository
from application.utils.path_resolver import resolve_asset_path
from config import Config


async def check_asset_paths(user_email: str = None):
    """Check if asset file paths exist on disk"""
    from infrastructure.database.models.asset_model import AssetModel
    
    repo = AssetRepository()
    
    # Get assets for user or all assets
    if user_email:
        assets = await repo.get_by_user_id(user_email, limit=100)
        print(f"\n📁 Checking assets for user: {user_email}")
    else:
        # Get all assets (limit to recent ones)
        assets = await AssetModel.find().sort(-AssetModel.created_at).limit(50).to_list()
        print(f"\n📁 Checking {len(assets)} recent assets")
    
    print(f"Base directory: {Config._BASE_DIR}\n")
    
    missing = []
    found = []
    
    for asset in assets:
        # Resolve path using utility function
        file_path = resolve_asset_path(asset.file_path)
        
        exists = file_path.exists()
        status = "✅" if exists else "❌"
        
        print(f"{status} {asset.file_name}")
        print(f"   Stored path: {asset.file_path}")
        print(f"   Resolved path: {file_path}")
        print(f"   User: {asset.user_id}")
        
        if exists:
            print(f"   Size: {file_path.stat().st_size / 1024:.1f} KB")
            found.append(asset)
        else:
            print(f"   ⚠️  FILE NOT FOUND")
            missing.append(asset)
        
        print()
    
    # Summary
    print("\n" + "="*60)
    print(f"Summary:")
    print(f"  ✅ Found: {len(found)}")
    print(f"  ❌ Missing: {len(missing)}")
    
    if missing:
        print(f"\n⚠️  Missing files:")
        for asset in missing:
            print(f"  - {asset.file_name} (ID: {asset.asset_id})")
    
    return found, missing


if __name__ == "__main__":
    import argparse
    from motor.motor_asyncio import AsyncIOMotorClient
    from beanie import init_beanie
    from infrastructure.database.models.asset_model import AssetModel
    
    parser = argparse.ArgumentParser(description="Check asset file paths")
    parser.add_argument("--email", help="User email to check (optional)")
    args = parser.parse_args()
    
    async def main():
        # Initialize database connection
        client = AsyncIOMotorClient(Config.MONGO_URI)
        db = client.get_default_database()
        
        # Initialize Beanie
        await init_beanie(database=db, document_models=[AssetModel])
        
        # Run the check
        await check_asset_paths(args.email)
        
        # Close connection
        client.close()
    
    asyncio.run(main())
