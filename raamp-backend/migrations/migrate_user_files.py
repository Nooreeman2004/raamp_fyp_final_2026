"""
Migration Script: Reorganize Uploaded Files by User
This script helps reorganize existing uploaded files into the new user-specific folder structure.

Usage:
    python migrations/migrate_user_files.py
"""
import os
import sys
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from application.utils.file_manager import FileManager

def migrate_files():
    """
    Migrate files from old flat structure to new user-specific structure.
    
    Old structure:
        uploaded_files/assets/*
        uploaded_files/brand_logos/*
    
    New structure:
        uploaded_files/{user_email}/content/*
        uploaded_files/{user_email}/logos/*
    """
    print("=" * 60)
    print("FILE STRUCTURE MIGRATION TOOL")
    print("=" * 60)
    print()
    print("This tool will help reorganize your uploaded files into")
    print("user-specific folders with proper organization.")
    print()
    print("⚠️  WARNING: This script does NOT automatically migrate files")
    print("   because we need user email information from your database.")
    print()
    print("📋 Manual Migration Steps:")
    print("   1. Query your database to get file-to-user mappings")
    print("   2. For each file, determine the owner's email")
    print("   3. Use FileManager.get_user_upload_path() to get target path")
    print("   4. Move the file to the new location")
    print()
    print("📁 New folder structure will be:")
    print("   /uploaded_files/")
    print("       /john_doe_gmail_com/")
    print("           /logos/")
    print("           /content/")
    print("       /jane_smith_yahoo_com/")
    print("           /logos/")
    print("           /content/")
    print()
    print("✨ Future uploads will automatically use this structure!")
    print("=" * 60)
    print()
    
    # Show current files
    base_dir = Path("uploaded_files")
    if base_dir.exists():
        print("Current files found:")
        for subdir in ['assets', 'brand_logos']:
            subdir_path = base_dir / subdir
            if subdir_path.exists():
                files = list(subdir_path.glob("*"))
                print(f"  - {subdir}/: {len(files)} files")
        print()
    
    # Example code
    print("Example migration code:")
    print("-" * 60)
    example_code = """
# Example: Migrate a logo for user john@example.com
from application.utils.file_manager import FileManager
from pathlib import Path
import shutil

user_email = "john@example.com"
old_logo_path = Path("uploaded_files/brand_logos/old_logo.png")

# Get new path
new_logo_dir = FileManager.get_user_upload_path(
    email=user_email,
    subfolder='logos',
    create=True
)
new_logo_path = new_logo_dir / "old_logo.png"

# Move file
shutil.move(str(old_logo_path), str(new_logo_path))
print(f"Moved: {old_logo_path} → {new_logo_path}")
"""
    print(example_code)
    print("-" * 60)
    print()
    print("✅ Your application is now ready to use organized storage!")
    print("   All new uploads will automatically use the new structure.")
    print()

if __name__ == "__main__":
    migrate_files()
