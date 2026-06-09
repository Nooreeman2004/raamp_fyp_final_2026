"""
⚡ Migrate Asset Paths
======================
Update asset file paths in database from legacy structure to new structure.

Legacy: generated_images/*, generated_reels/*, generated_videos/*
New: generated_assets/images/*, generated_assets/reels/*, generated_assets/videos/*

This is optional - the code now handles both formats automatically.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from infrastructure.database.models.asset_model import AssetModel
from config import Config


async def migrate_asset_paths(dry_run: bool = True):
    """Migrate asset paths from legacy to new structure"""
    
    # Initialize database
    client = AsyncIOMotorClient(Config.MONGO_URI)
    db = client.get_default_database()
    await init_beanie(database=db, document_models=[AssetModel])
    
    print(f"\n{'🔍 DRY RUN MODE' if dry_run else '✏️  MIGRATION MODE'}")
    print("="*60)
    
    # Find all assets with legacy paths
    legacy_patterns = ["generated_images", "generated_reels", "generated_videos"]
    
    total_updated = 0
    
    for pattern in legacy_patterns:
        # Find assets with this pattern
        assets = await AssetModel.find(
            AssetModel.file_path.regex(f"^{pattern}")
        ).to_list()
        
        if not assets:
            print(f"\n✓ No assets found with pattern: {pattern}")
            continue
        
        print(f"\n📁 Found {len(assets)} assets with pattern: {pattern}")
        
        for asset in assets:
            old_path = asset.file_path
            
            # Map to new structure
            if old_path.startswith("generated_images"):
                new_path = old_path.replace("generated_images", "generated_assets/images", 1)
            elif old_path.startswith("generated_reels"):
                new_path = old_path.replace("generated_reels", "generated_assets/reels", 1)
            elif old_path.startswith("generated_videos"):
                new_path = old_path.replace("generated_videos", "generated_assets/videos", 1)
            else:
                continue
            
            # Verify new path exists on disk
            full_path = Config._BASE_DIR / new_path
            if not full_path.exists():
                print(f"  ⚠️  Skipping {asset.file_name} - file not found at {full_path}")
                continue
            
            print(f"  {asset.file_name}")
            print(f"    Old: {old_path}")
            print(f"    New: {new_path}")
            
            if not dry_run:
                asset.file_path = new_path
                await asset.save()
                print(f"    ✅ Updated")
            
            total_updated += 1
    
    print("\n" + "="*60)
    print(f"Summary:")
    print(f"  Total assets to update: {total_updated}")
    
    if dry_run:
        print(f"\n💡 This was a dry run. Run with --apply to actually update the database.")
    else:
        print(f"\n✅ Migration complete!")
    
    client.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate asset paths to new structure")
    parser.add_argument("--apply", action="store_true", help="Actually apply changes (default is dry run)")
    args = parser.parse_args()
    
    asyncio.run(migrate_asset_paths(dry_run=not args.apply))
