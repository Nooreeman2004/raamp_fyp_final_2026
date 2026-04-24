"""
Validation Script: Verify generated_assets/ structure
=====================================================
This script validates that the refactored directory structure is working correctly.

Checks:
1. All directories exist
2. Directories are readable/writable
3. Config paths are accessible
4. Sample files can be created
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

def check_directory_exists(path: Path, name: str) -> bool:
    """Check if directory exists"""
    if not path.exists():
        print(f"   ❌ {name}: Does not exist - {path}")
        return False
    
    if not path.is_dir():
        print(f"   ❌ {name}: Exists but is not a directory - {path}")
        return False
    
    print(f"   ✅ {name}: {path}")
    return True


def check_directory_writable(path: Path, name: str) -> bool:
    """Check if directory is writable"""
    test_file = path / ".write_test"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print(f"   ✅ {name}: Writable")
        return True
    except Exception as e:
        print(f"   ❌ {name}: Not writable - {e}")
        return False


def count_files_in_directory(path: Path) -> int:
    """Count files in directory recursively"""
    if not path.exists():
        return 0
    return sum(1 for _ in path.rglob('*') if _.is_file())


def main():
    """Run all validation checks"""
    print("🔍 VALIDATING GENERATED ASSETS STRUCTURE")
    print("=" * 60)
    
    all_checks_passed = True
    
    # 1. Check base directory
    print("\n1️⃣  BASE DIRECTORY:")
    if not check_directory_exists(Config.GENERATED_ASSETS_DIR, "generated_assets"):
        all_checks_passed = False
        print("\n❌ CRITICAL: Base directory does not exist!")
        print("   Run: python scripts/migrate_to_generated_assets.py")
        return False
    
    # 2. Check subdirectories
    print("\n2️⃣  SUBDIRECTORIES:")
    subdirs = {
        "Images": Config.GENERATED_IMAGES_DIR,
        "Videos": Config.GENERATED_VIDEOS_DIR,
        "Reels": Config.GENERATED_REELS_DIR,
        "Uploads": Config.UPLOADED_FILES_DIR,
    }
    
    for name, path in subdirs.items():
        if not check_directory_exists(path, name):
            all_checks_passed = False
    
    # 3. Check write permissions
    print("\n3️⃣  WRITE PERMISSIONS:")
    for name, path in subdirs.items():
        if path.exists():
            if not check_directory_writable(path, name):
                all_checks_passed = False
        else:
            print(f"   ⏭️  {name}: Skipped (directory doesn't exist)")
    
    # 4. Count existing files
    print("\n4️⃣  EXISTING CONTENT:")
    total_files = 0
    for name, path in subdirs.items():
        count = count_files_in_directory(path)
        total_files += count
        
        if count == 0:
            print(f"   📭 {name}: Empty")
        else:
            print(f"   📦 {name}: {count} files")
    
    print(f"\n   Total files: {total_files}")
    
    # 5. Verify no old directories exist
    print("\n5️⃣  OLD DIRECTORIES:")
    old_dirs = ["generated_images", "generated_reels", "generated_videos", "uploaded_files"]
    old_dirs_found = False
    
    base_dir = Config.GENERATED_ASSETS_DIR.parent  # raamp-backend directory
    
    for old_dir in old_dirs:
        old_path = base_dir / old_dir
        if old_path.exists():
            print(f"   ⚠️  WARNING: Old directory still exists: {old_dir}")
            old_dirs_found = True
        else:
            print(f"   ✅ {old_dir}: Removed")
    
    if old_dirs_found:
        print("\n   ⚠️  Consider removing old directories to avoid confusion")
    
    # 6. Config validation
    print("\n6️⃣  CONFIG VALIDATION:")
    try:
        # Check that Config attributes are Path objects
        assert isinstance(Config.GENERATED_ASSETS_DIR, Path), "GENERATED_ASSETS_DIR is not a Path"
        assert isinstance(Config.GENERATED_IMAGES_DIR, Path), "GENERATED_IMAGES_DIR is not a Path"
        assert isinstance(Config.GENERATED_VIDEOS_DIR, Path), "GENERATED_VIDEOS_DIR is not a Path"
        assert isinstance(Config.GENERATED_REELS_DIR, Path), "GENERATED_REELS_DIR is not a Path"
        assert isinstance(Config.UPLOADED_FILES_DIR, Path), "UPLOADED_FILES_DIR is not a Path"
        
        print("   ✅ All Config paths are Path objects")
        
        # Check ensure_asset_directories method exists
        assert hasattr(Config, 'ensure_asset_directories'), "ensure_asset_directories method missing"
        print("   ✅ Config.ensure_asset_directories() method exists")
        
        # Test the method
        Config.ensure_asset_directories()
        print("   ✅ Config.ensure_asset_directories() runs successfully")
        
    except AssertionError as e:
        print(f"   ❌ Config validation failed: {e}")
        all_checks_passed = False
    except Exception as e:
        print(f"   ❌ Error validating config: {e}")
        all_checks_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_checks_passed and not old_dirs_found:
        print("✅ ALL CHECKS PASSED!")
        print("   The refactored structure is ready to use.")
    elif all_checks_passed:
        print("⚠️  CHECKS PASSED WITH WARNINGS")
        print("   Consider cleaning up old directories.")
    else:
        print("❌ SOME CHECKS FAILED")
        print("   Review errors above and fix issues.")
    
    print("=" * 60)
    
    # Next steps
    print("\n📝 NEXT STEPS:")
    if all_checks_passed:
        print("   1. ✅ Directory structure is valid")
        print("   2. Start backend: python main.py")
        print("   3. Test endpoints that serve static assets")
        print("   4. Verify file uploads and generation work correctly")
    else:
        print("   1. Fix errors listed above")
        print("   2. Re-run this validation script")
    
    print()
    return all_checks_passed


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Validation script crashed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
