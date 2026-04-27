"""
📁 Path Resolver Utility
========================
Handles resolution of asset file paths, including legacy path mapping.

Legacy structure: generated_images/*, generated_reels/*, generated_videos/*
New structure: generated_assets/images/*, generated_assets/reels/*, generated_assets/videos/*
"""

from pathlib import Path
from typing import Union
from config import Config


def resolve_asset_path(file_path: Union[str, Path]) -> Path:
    """
    Resolve an asset file path, handling both absolute and relative paths,
    and mapping legacy paths to the new structure.
    
    Args:
        file_path: File path from database (can be absolute or relative)
        
    Returns:
        Resolved absolute Path object
        
    Examples:
        >>> resolve_asset_path("generated_images/20260310_065838/variation_2.png")
        Path("D:/raamp-backend/generated_assets/images/20260310_065838/variation_2.png")
        
        >>> resolve_asset_path("generated_assets/images/20260310_065838/variation_2.png")
        Path("D:/raamp-backend/generated_assets/images/20260310_065838/variation_2.png")
    """
    path = Path(file_path)
    
    # If already absolute, return as-is
    if path.is_absolute():
        return path
    
    # Try new structure first
    resolved_path = Config._BASE_DIR / file_path
    if resolved_path.exists():
        return resolved_path
    
    # Try legacy path mapping
    legacy_path = str(file_path)
    
    if legacy_path.startswith("generated_images"):
        new_path = legacy_path.replace("generated_images", "generated_assets/images", 1)
        resolved_path = Config._BASE_DIR / new_path
        if resolved_path.exists():
            return resolved_path
    
    elif legacy_path.startswith("generated_reels"):
        new_path = legacy_path.replace("generated_reels", "generated_assets/reels", 1)
        resolved_path = Config._BASE_DIR / new_path
        if resolved_path.exists():
            return resolved_path
    
    elif legacy_path.startswith("generated_videos"):
        new_path = legacy_path.replace("generated_videos", "generated_assets/videos", 1)
        resolved_path = Config._BASE_DIR / new_path
        if resolved_path.exists():
            return resolved_path
    
    # Return the original resolved path even if it doesn't exist
    # (caller can check existence and handle appropriately)
    return Config._BASE_DIR / file_path


def get_legacy_path_mapping(legacy_path: str) -> str:
    """
    Get the new path for a legacy path without checking existence.
    
    Args:
        legacy_path: Legacy path string
        
    Returns:
        New path string
        
    Examples:
        >>> get_legacy_path_mapping("generated_images/test.png")
        "generated_assets/images/test.png"
    """
    if legacy_path.startswith("generated_images"):
        return legacy_path.replace("generated_images", "generated_assets/images", 1)
    elif legacy_path.startswith("generated_reels"):
        return legacy_path.replace("generated_reels", "generated_assets/reels", 1)
    elif legacy_path.startswith("generated_videos"):
        return legacy_path.replace("generated_videos", "generated_assets/videos", 1)
    else:
        return legacy_path
