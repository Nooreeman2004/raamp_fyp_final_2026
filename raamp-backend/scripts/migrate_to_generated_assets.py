"""
Migration Script: Refactor to generated_assets/ directory structure
=================================================================
This script moves all generated and uploaded assets to a centralized location.

Structure:
- generated_images/ → generated_assets/images/
- generated_reels/ → generated_assets/reels/
- generated_videos/ → generated_assets/videos/
- uploaded_files/ → generated_assets/uploads/
"""

import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Base directory (raamp-backend/)
BASE_DIR = Path(__file__).parent.parent
GENERATED_ASSETS_DIR = BASE_DIR / "generated_assets"

# Migration mapping: old_path → new_path
MIGRATIONS = {
    "generated_images": "generated_assets/images",
    "generated_reels": "generated_assets/reels",
    "generated_videos": "generated_assets/videos",
    "uploaded_files": "generated_assets/uploads",
}


def move_directory(old_path: Path, new_path: Path) -> bool:
    """
    Move directory with all contents. If new_path exists, merge contents.
    
    Args:
        old_path: Source directory
        new_path: Destination directory
        
    Returns:
        True if moved/merged successfully, False if source doesn't exist
    """
    if not old_path.exists():
        logger.info(f"⏩ SKIP: {old_path} does not exist")
        return False
    
    if not old_path.is_dir():
        logger.warning(f"⚠️  {old_path} is not a directory, skipping")
        return False
    
    # Create parent directory
    new_path.parent.mkdir(parents=True, exist_ok=True)
    
    if new_path.exists():
        logger.info(f"📁 MERGE: {old_path} → {new_path} (destination exists)")
        # Merge: copy files from old to new, then remove old
        for item in old_path.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(old_path)
                dest_file = new_path / relative_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                if dest_file.exists():
                    logger.warning(f"   ⚠️  File exists, keeping existing: {dest_file}")
                else:
                    shutil.copy2(item, dest_file)
                    logger.info(f"   ✅ Copied: {relative_path}")
        
        # Remove old directory after merging
        shutil.rmtree(old_path)
        logger.info(f"   🗑️  Removed old directory: {old_path}")
    else:
        # Move entire directory
        logger.info(f"📦 MOVE: {old_path} → {new_path}")
        shutil.move(str(old_path), str(new_path))
        logger.info(f"   ✅ Moved successfully")
    
    return True


def create_empty_directories():
    """Create empty directory structure if nothing exists"""
    logger.info("📁 Creating directory structure...")
    
    directories = [
        GENERATED_ASSETS_DIR / "images",
        GENERATED_ASSETS_DIR / "reels",
        GENERATED_ASSETS_DIR / "videos",
        GENERATED_ASSETS_DIR / "uploads",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"   ✅ {directory} ready")


def validate_migration():
    """Validate that migration was successful"""
    logger.info("\n🔍 VALIDATION:")
    
    all_good = True
    
    # Check new directories exist
    expected_dirs = [
        GENERATED_ASSETS_DIR / "images",
        GENERATED_ASSETS_DIR / "reels",
        GENERATED_ASSETS_DIR / "videos",
        GENERATED_ASSETS_DIR / "uploads",
    ]
    
    for directory in expected_dirs:
        if directory.exists() and directory.is_dir():
            file_count = len(list(directory.rglob('*')))
            logger.info(f"   ✅ {directory.relative_to(BASE_DIR)} ({file_count} items)")
        else:
            logger.error(f"   ❌ {directory.relative_to(BASE_DIR)} missing!")
            all_good = False
    
    # Check old directories removed
    for old_dir in MIGRATIONS.keys():
        old_path = BASE_DIR / old_dir
        if old_path.exists():
            logger.warning(f"   ⚠️  Old directory still exists: {old_dir}")
        else:
            logger.info(f"   ✅ Old directory removed: {old_dir}")
    
    return all_good


def main():
    """Execute the migration"""
    logger.info("🚀 Starting migration to generated_assets/")
    logger.info(f"📍 Base directory: {BASE_DIR}\n")
    
    # Perform migrations
    logger.info("📦 MOVING DIRECTORIES:")
    moved_count = 0
    
    for old_dir, new_dir in MIGRATIONS.items():
        old_path = BASE_DIR / old_dir
        new_path = BASE_DIR / new_dir
        
        if move_directory(old_path, new_path):
            moved_count += 1
    
    # Ensure all directories exist (even if empty)
    create_empty_directories()
    
    # Validate
    success = validate_migration()
    
    # Summary
    logger.info("\n" + "="*60)
    if success:
        logger.info("✅ MIGRATION COMPLETE!")
        logger.info(f"   Moved/merged {moved_count} directories")
        logger.info(f"   All assets now in: generated_assets/")
    else:
        logger.error("❌ MIGRATION HAD ISSUES - Check logs above")
    
    logger.info("="*60)
    
    logger.info("\n📝 NEXT STEPS:")
    logger.info("   1. Verify files in generated_assets/ subdirectories")
    logger.info("   2. Start backend: python main.py")
    logger.info("   3. Test endpoints that use these assets")
    logger.info("   4. If everything works, the migration is complete!\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        exit(1)
