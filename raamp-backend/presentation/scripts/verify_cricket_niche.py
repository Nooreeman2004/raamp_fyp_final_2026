#!/usr/bin/env python3
"""
Verification Script: Check Niche Values for Cricket Trends

This script helps verify that cricket/sports trends are being stored
with the correct niche value after scanning.

Usage:
    python scripts/verify_cricket_niche.py [--keyword "cricket"]
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from infrastructure.database.models.trend_signal_model import TrendSignalModel
from config import Config

# Get MongoDB URL from config
MONGODB_URL = Config.MONGO_URI


async def check_recent_cricket_trends(hours: int = 24, keyword_filter: str = None):
    """Check recent cricket/sports trends and their niche values."""
    print("\n" + "="*80)
    print("CRICKET/SPORTS NICHE VERIFICATION")
    print("="*80)
    print(f"Checking trends from the last {hours} hours")
    if keyword_filter:
        print(f"Filtering for keyword: '{keyword_filter}'")
    print("="*80)
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Check trend_detections
    print("\n📊 TREND DETECTIONS:")
    print("-" * 80)
    
    query = {"detected_at": {"$gte": cutoff_time}}
    if keyword_filter:
        query["keyword"] = {"$regex": keyword_filter, "$options": "i"}
    
    detections = await TrendDetectionModel.find(query).sort("-detected_at").to_list()
    
    if not detections:
        print(f"No trend detections found in the last {hours} hours")
    else:
        # Filter for cricket/sports keywords
        cricket_keywords = ['cricket', 'psl', 'ipl', 'babar', 'shaheen', 'sports', 
                           'football', 'match', 'player', 'tournament']
        
        cricket_detections = [
            d for d in detections 
            if any(kw in d.keyword.lower() for kw in cricket_keywords)
        ]
        
        if not cricket_detections:
            print(f"No cricket/sports trends found in {len(detections)} total detections")
        else:
            print(f"Found {len(cricket_detections)} cricket/sports trends out of {len(detections)} total\n")
            
            # Display results
            print(f"{'Keyword':<42} {'Niche':<12} {'User':<32} {'Detected At':<18} {'Impact':<8} {'Value':<8}")
            print("-" * 130)
            
            for d in cricket_detections[:20]:  # Show first 20
                keyword_display = d.keyword[:40] + ".." if len(d.keyword) > 40 else d.keyword
                user_display = d.user_id[:30] + ".." if len(d.user_id) > 30 else d.user_id
                detected_display = d.detected_at.strftime("%Y-%m-%d %H:%M")
                
                print(f"{keyword_display:<42} {d.niche:<12} {user_display:<32} {detected_display:<18} {d.impact_level:<8} {d.current_value:<8.1f}")
            
            # Check for incorrect niche values
            incorrect = [d for d in cricket_detections if d.niche.lower() == 'fashion']
            if incorrect:
                print(f"\n⚠️  WARNING: Found {len(incorrect)} cricket/sports trends with niche='fashion':")
                for d in incorrect:
                    print(f"   - '{d.keyword}' (user: {d.user_id})")
            else:
                print(f"\n✓ All cricket/sports trends have correct niche values (not 'fashion')")
    
    # Check trend_signals
    print("\n\n📊 TREND SIGNALS:")
    print("-" * 80)
    
    query = {"created_at": {"$gte": cutoff_time}}
    signals = await TrendSignalModel.find(query).sort("-created_at").to_list()
    
    if not signals:
        print(f"No trend signals found in the last {hours} hours")
    else:
        # Filter for cricket/sports keywords
        cricket_signals = []
        for s in signals:
            has_cricket = any(
                any(kw in keyword.lower() for kw in cricket_keywords)
                for keyword in s.keywords
            )
            if has_cricket:
                cricket_signals.append(s)
        
        if not cricket_signals:
            print(f"No cricket/sports trends found in {len(signals)} total signals")
        else:
            print(f"Found {len(cricket_signals)} cricket/sports signals out of {len(signals)} total\n")
            
            # Display results
            print(f"{'Keywords':<42} {'Niche':<12} {'User':<32} {'Created At':<18} {'Status':<12} {'Location':<10}")
            print("-" * 130)
            
            for s in cricket_signals[:20]:  # Show first 20
                cricket_kws = [kw for kw in s.keywords if any(ck in kw.lower() for ck in cricket_keywords)]
                kw_display = ", ".join(cricket_kws[:2])
                kw_display = kw_display[:40] + ".." if len(kw_display) > 40 else kw_display
                user_display = s.user_email[:30] + ".." if len(s.user_email) > 30 else s.user_email
                created_display = s.created_at.strftime("%Y-%m-%d %H:%M")
                
                print(f"{kw_display:<42} {s.niche:<12} {user_display:<32} {created_display:<18} {s.fetch_status:<12} {s.location:<10}")
            
            # Check for incorrect niche values
            incorrect = [s for s in cricket_signals if s.niche.lower() == 'fashion']
            if incorrect:
                print(f"\n⚠️  WARNING: Found {len(incorrect)} cricket/sports signals with niche='fashion':")
                for s in incorrect:
                    print(f"   - User: {s.user_email}, Keywords: {s.keywords[:3]}")
            else:
                print(f"\n✓ All cricket/sports signals have correct niche values (not 'fashion')")


async def check_specific_keyword(keyword: str):
    """Check all records for a specific keyword."""
    print("\n" + "="*80)
    print(f"CHECKING KEYWORD: '{keyword}'")
    print("="*80)
    
    # Check detections
    detections = await TrendDetectionModel.find(
        {"keyword": {"$regex": keyword, "$options": "i"}}
    ).sort("-detected_at").limit(10).to_list()
    
    print(f"\nFound {len(detections)} detections for '{keyword}':")
    if detections:
        for d in detections:
            print(f"\n  Keyword: {d.keyword}")
            print(f"  Niche: {d.niche}")
            print(f"  User: {d.user_id}")
            print(f"  Detected: {d.detected_at}")
            print(f"  Status: {d.status}")
            
            if d.niche.lower() == 'fashion':
                print(f"  ⚠️  INCORRECT NICHE: Should be 'sports', not 'fashion'")
    
    # Check signals
    signals = await TrendSignalModel.find(
        {"keywords": {"$regex": keyword, "$options": "i"}}
    ).sort("-created_at").limit(10).to_list()
    
    print(f"\nFound {len(signals)} signals containing '{keyword}':")
    if signals:
        for s in signals:
            matching_kws = [kw for kw in s.keywords if keyword.lower() in kw.lower()]
            print(f"\n  Keywords: {matching_kws}")
            print(f"  Niche: {s.niche}")
            print(f"  User: {s.user_email}")
            print(f"  Created: {s.created_at}")
            print(f"  Status: {s.fetch_status}")
            
            if s.niche.lower() == 'fashion':
                print(f"  ⚠️  INCORRECT NICHE: Should be 'sports', not 'fashion'")


async def main():
    """Main verification function."""
    print("\n" + "="*80)
    print("CRICKET/SPORTS NICHE VERIFICATION TOOL")
    print("="*80)
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    
    # Parse arguments
    keyword_filter = None
    hours = 24
    
    for i, arg in enumerate(sys.argv):
        if arg in ["--keyword", "-k"] and i + 1 < len(sys.argv):
            keyword_filter = sys.argv[i + 1]
        elif arg in ["--hours", "-h"] and i + 1 < len(sys.argv):
            hours = int(sys.argv[i + 1])
    
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
        
        # Run verification
        if keyword_filter:
            await check_specific_keyword(keyword_filter)
        
        await check_recent_cricket_trends(hours=hours, keyword_filter=keyword_filter)
        
        print("\n" + "="*80)
        print("VERIFICATION COMPLETE")
        print("="*80)
        print("\nNext steps:")
        print("1. If you see incorrect niche values, run the migration:")
        print("   python scripts/fix_cricket_niche_migration.py --dry-run")
        print("   python scripts/fix_cricket_niche_migration.py")
        print("\n2. Clear frontend cache to see fresh data:")
        print("   Use the 'CLEAR CACHE' button in the Trend Arbitrage page")
        print("\n3. Run a fresh scan and verify the niche is correct")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
