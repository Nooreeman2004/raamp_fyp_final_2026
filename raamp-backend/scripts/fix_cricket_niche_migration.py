#!/usr/bin/env python3
"""
Migration Script: Fix Cricket/Sports Trends Incorrectly Tagged as Fashion

This script identifies and corrects trend records where:
- niche='fashion' (or case variations)
- keyword contains cricket/sports-related terms

Updates both:
1. trend_detections collection
2. trend_signals collection

Usage:
    python scripts/fix_cricket_niche_migration.py [--dry-run]
"""

import asyncio
import sys
import os
import re
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from infrastructure.database.models.trend_signal_model import TrendSignalModel
from config import Config

# Get MongoDB URL from config
MONGODB_URL = Config.MONGO_URI


# Cricket and sports-related keywords to detect
CRICKET_SPORTS_KEYWORDS = [
    # Cricket specific
    r'\bcricket\b', r'\bpsl\b', r'\bipl\b', r'\btest match\b', r'\bodi\b', r'\bt20\b',
    r'\bbowler\b', r'\bbatsman\b', r'\bwicket\b', r'\bstumps\b', r'\binnings\b',
    r'\bbabar azam\b', r'\bbabarazam\b', r'\bshadab\b', r'\brizwan\b', r'\bshaheen\b',
    r'\bpakistan cricket\b', r'\bpak vs\b', r'\bvs pak\b',
    r'\bzadran\b', r'\bcricketer\b',
    
    # Team abbreviations and match scores
    r'\brwp vs\b', r'\bisu\b', r'\blah vs\b', r'\bqg\b', r'\bms\b', r'\brap vs\b',
    r'\bmi vs\b', r'\bgt\b', r'\bkkr vs\b', r'\bsrh vs\b', r'\bdc\b', r'\brcb\b',
    r'\bpeshawar zalmi\b', r'\bquetta gladiators\b', r'\blahore qalandars\b',
    r'\bmultan sultans\b', r'\bislamabad united\b', r'\bkarachi kings\b',
    r'\bpindiz\b', r'\bhyderabad kingsmen\b',
    
    # Match-related terms
    r'\bvs\b.*\bscore\b', r'\bstandings\b', r'\bpoints table\b', r'\blive\b.*\bmatch\b',
    
    # General sports
    r'\bfootball\b', r'\bsoccer\b', r'\bbasketball\b', r'\btennis\b', r'\bhockey\b',
    r'\bsports\b', r'\bplayer\b', r'\bmatch\b', r'\btournament\b', r'\bchampionship\b',
    r'\bleague\b', r'\bteam\b', r'\bgoal\b', r'\bscore\b', r'\bgame\b',
    r'\bworld cup\b', r'\basia cup\b',
    
    # Country vs country (sports matches)
    r'\buae vs\b', r'\bnepal vs\b', r'\bafghanistan vs\b', r'\bbangladesh vs\b',
    
    # Sports brands/equipment
    r'\bsports wear\b', r'\bsports gear\b', r'\bcricket bat\b', r'\bcricket ball\b',
]


def is_cricket_sports_keyword(keyword: str) -> bool:
    """Check if keyword contains cricket or sports-related terms."""
    keyword_lower = keyword.lower()
    
    for pattern in CRICKET_SPORTS_KEYWORDS:
        if re.search(pattern, keyword_lower):
            return True
    
    return False


def determine_correct_niche(keyword: str) -> str:
    """Determine the correct niche based on keyword content."""
    keyword_lower = keyword.lower()
    
    # Check for cricket-specific terms
    cricket_terms = [r'\bcricket\b', r'\bpsl\b', r'\bipl\b', r'\bbabar azam\b', 
                     r'\bwicket\b', r'\bbowler\b', r'\bbatsman\b']
    for pattern in cricket_terms:
        if re.search(pattern, keyword_lower):
            return "sports"
    
    # Check for general sports
    sports_terms = [r'\bfootball\b', r'\bsoccer\b', r'\bbasketball\b', 
                    r'\btennis\b', r'\bhockey\b', r'\bsports\b']
    for pattern in sports_terms:
        if re.search(pattern, keyword_lower):
            return "sports"
    
    # Default to sports if we got here (matched the broader patterns)
    return "sports"


async def fix_trend_detections(dry_run: bool = True) -> dict:
    """Fix niche values in trend_detections collection."""
    print("\n" + "="*70)
    print("FIXING TREND_DETECTIONS COLLECTION")
    print("="*70)
    
    # Find all records with fashion niche
    fashion_trends = await TrendDetectionModel.find(
        {"niche": {"$regex": "^fashion$", "$options": "i"}}
    ).to_list()
    
    print(f"\nFound {len(fashion_trends)} records with niche='fashion'")
    
    # Filter for cricket/sports keywords
    to_fix = []
    for trend in fashion_trends:
        if is_cricket_sports_keyword(trend.keyword):
            correct_niche = determine_correct_niche(trend.keyword)
            to_fix.append({
                "record": trend,
                "keyword": trend.keyword,
                "current_niche": trend.niche,
                "correct_niche": correct_niche,
                "user_id": trend.user_id,
                "detected_at": trend.detected_at
            })
    
    print(f"\nFound {len(to_fix)} records with cricket/sports keywords incorrectly tagged as fashion")
    
    if to_fix:
        print("\nSample records to fix:")
        for item in to_fix[:10]:  # Show first 10
            print(f"  - Keyword: '{item['keyword']}'")
            print(f"    User: {item['user_id']}")
            print(f"    Current niche: {item['current_niche']} → Correct niche: {item['correct_niche']}")
            print(f"    Detected at: {item['detected_at']}")
            print()
    
    if dry_run:
        print(f"\n[DRY RUN] Would update {len(to_fix)} records in trend_detections")
        return {"collection": "trend_detections", "dry_run": True, "count": len(to_fix)}
    
    # Perform actual updates
    updated_count = 0
    for item in to_fix:
        try:
            trend = item["record"]
            trend.niche = item["correct_niche"]
            await trend.save()
            updated_count += 1
        except Exception as e:
            print(f"Error updating trend {item['keyword']}: {e}")
    
    print(f"\n✓ Updated {updated_count} records in trend_detections")
    return {"collection": "trend_detections", "dry_run": False, "count": updated_count}


async def fix_trend_signals(dry_run: bool = True) -> dict:
    """Fix niche values in trend_signals collection."""
    print("\n" + "="*70)
    print("FIXING TREND_SIGNALS COLLECTION")
    print("="*70)
    
    # Find all records with fashion niche
    fashion_signals = await TrendSignalModel.find(
        {"niche": {"$regex": "^fashion$", "$options": "i"}}
    ).to_list()
    
    print(f"\nFound {len(fashion_signals)} records with niche='fashion'")
    
    # Filter for cricket/sports keywords in the keywords array
    to_fix = []
    for signal in fashion_signals:
        # Check if any keyword in the keywords list is cricket/sports related
        has_sports_keyword = any(is_cricket_sports_keyword(kw) for kw in signal.keywords)
        
        if has_sports_keyword:
            # Determine correct niche from the keywords
            correct_niche = "sports"
            for kw in signal.keywords:
                if is_cricket_sports_keyword(kw):
                    correct_niche = determine_correct_niche(kw)
                    break
            
            to_fix.append({
                "record": signal,
                "keywords": signal.keywords,
                "current_niche": signal.niche,
                "correct_niche": correct_niche,
                "user_email": signal.user_email,
                "created_at": signal.created_at
            })
    
    print(f"\nFound {len(to_fix)} records with cricket/sports keywords incorrectly tagged as fashion")
    
    if to_fix:
        print("\nSample records to fix:")
        for item in to_fix[:10]:  # Show first 10
            print(f"  - Keywords: {item['keywords'][:3]}...")  # Show first 3 keywords
            print(f"    User: {item['user_email']}")
            print(f"    Current niche: {item['current_niche']} → Correct niche: {item['correct_niche']}")
            print(f"    Created at: {item['created_at']}")
            print()
    
    if dry_run:
        print(f"\n[DRY RUN] Would update {len(to_fix)} records in trend_signals")
        return {"collection": "trend_signals", "dry_run": True, "count": len(to_fix)}
    
    # Perform actual updates
    updated_count = 0
    for item in to_fix:
        try:
            signal = item["record"]
            signal.niche = item["correct_niche"]
            await signal.save()
            updated_count += 1
        except Exception as e:
            print(f"Error updating signal for user {item['user_email']}: {e}")
    
    print(f"\n✓ Updated {updated_count} records in trend_signals")
    return {"collection": "trend_signals", "dry_run": False, "count": updated_count}


async def main():
    """Main migration function."""
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    
    print("\n" + "="*70)
    print("CRICKET/SPORTS NICHE MIGRATION")
    print("="*70)
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (will update database)'}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    print("="*70)
    
    # Connect to MongoDB
    print("\nConnecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    
    try:
        # Initialize Beanie
        await init_beanie(
            database=client.get_database(),
            document_models=[TrendDetectionModel, TrendSignalModel]
        )
        print("✓ Connected to database")
        
        # Run migrations
        results = []
        
        # Fix trend_detections
        result1 = await fix_trend_detections(dry_run=dry_run)
        results.append(result1)
        
        # Fix trend_signals
        result2 = await fix_trend_signals(dry_run=dry_run)
        results.append(result2)
        
        # Summary
        print("\n" + "="*70)
        print("MIGRATION SUMMARY")
        print("="*70)
        for result in results:
            status = "Would update" if result["dry_run"] else "Updated"
            print(f"{result['collection']}: {status} {result['count']} records")
        
        if dry_run:
            print("\nThis was a DRY RUN. No changes were made.")
            print("Run without --dry-run flag to apply changes:")
            print("  python scripts/fix_cricket_niche_migration.py")
        else:
            print("\n✓ Migration completed successfully!")
        
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
