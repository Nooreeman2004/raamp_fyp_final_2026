"""
Direct MongoDB query to check trend AI analysis status
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv('.env')

# Try to get MongoDB URI from environment or use default
mongodb_uri = os.getenv('MONGODB_URL') or os.getenv('MONGODB_URI') or os.getenv('MONGO_URI') or 'mongodb://localhost:27017'
db_name = 'raamp_db'

print('='*70)
print('DIRECT DATABASE CHECK - INTELLIGENCE GRID')
print('='*70)
print(f'\nConnecting to: {mongodb_uri[:50]}...')
print(f'Database: {db_name}')

try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    # Test connection
    client.server_info()
    print('✅ Connected to MongoDB\n')
    
    db = client[db_name]
    
    # 1. Check recent trend detections
    print('1. RECENT TREND DETECTIONS:')
    print('-'*70)
    trends = list(db.trend_detections.find().sort('detected_at', -1).limit(5))
    
    if not trends:
        print('❌ NO TRENDS FOUND IN DATABASE')
    else:
        print(f'Found {len(trends)} recent trends:\n')
        for i, trend in enumerate(trends, 1):
            print(f'Trend {i}:')
            print(f'  Keyword: {trend.get("keyword")}')
            print(f'  Niche: {trend.get("niche")}')
            print(f'  Location: {trend.get("location")}')
            print(f'  Trend Signal ID: {trend.get("trend_signal_id")}')
            print(f'  Detected: {trend.get("detected_at")}')
            print()
    
    # 2. Check AI analysis records
    print('\n2. AI ANALYSIS RECORDS:')
    print('-'*70)
    
    if trends:
        signal_ids = [str(t.get('trend_signal_id')) for t in trends if t.get('trend_signal_id')]
        
        if signal_ids:
            analyses = list(db.trend_ai_analyses.find({'trend_id': {'$in': signal_ids}}))
            
            if not analyses:
                print('❌ NO AI ANALYSIS RECORDS FOUND')
                print(f'   Searched for trend_signal_ids: {signal_ids[:3]}...')
                print('\n🔍 ROOT CAUSE: AI analysis has never been triggered')
            else:
                print(f'Found {len(analyses)} AI analysis records:\n')
                
                for i, analysis in enumerate(analyses, 1):
                    print(f'Analysis {i}:')
                    print(f'  Trend ID: {analysis.get("trend_id")}')
                    print(f'  Keyword: {analysis.get("trend_keyword")}')
                    print(f'  Status: {analysis.get("status")}')
                    
                    if analysis.get('status') == 'failed':
                        print(f'  ❌ Error: {analysis.get("error_message")}')
                    
                    if analysis.get('status') == 'completed':
                        campaign_ideas = analysis.get('campaign_ideas', [])
                        growth_hacks = analysis.get('growth_hacks', [])
                        
                        print(f'  Campaign Ideas: {len(campaign_ideas)} items')
                        if campaign_ideas:
                            print(f'    - First: {campaign_ideas[0].get("title", "N/A")[:50]}')
                        else:
                            print(f'    ⚠️  EMPTY ARRAY')
                        
                        print(f'  Growth Hacks: {len(growth_hacks)} items')
                        if growth_hacks:
                            print(f'    - First: {growth_hacks[0][:50]}...')
                        else:
                            print(f'    ⚠️  EMPTY ARRAY')
                        
                        if not campaign_ideas and not growth_hacks:
                            print('\n  🔍 ROOT CAUSE: LLM returned empty arrays')
                    
                    print(f'  Generated: {analysis.get("generated_at")}')
                    print()
        else:
            print('❌ No trend_signal_ids found in trend detections')
    
    # 3. Check trend signals with ai_analysis_status
    print('\n3. TREND SIGNALS (with ai_analysis_status):')
    print('-'*70)
    signals = list(db.trend_signals.find().sort('created_at', -1).limit(5))
    
    if not signals:
        print('❌ NO TREND SIGNALS FOUND')
    else:
        print(f'Found {len(signals)} recent signals:\n')
        for i, signal in enumerate(signals, 1):
            print(f'Signal {i}:')
            print(f'  ID: {signal.get("_id")}')
            print(f'  User: {signal.get("user_email")}')
            print(f'  Niche: {signal.get("niche")}')
            print(f'  Location: {signal.get("location")}')
            print(f'  Keywords: {signal.get("keywords", [])[:3]}')
            print(f'  Fetch Status: {signal.get("fetch_status")}')
            
            # Check if ai_analysis_status field exists
            if 'ai_analysis_status' in signal:
                print(f'  ✅ ai_analysis_status: {signal.get("ai_analysis_status")}')
            else:
                print(f'  ⚠️  ai_analysis_status: FIELD DOES NOT EXIST')
            
            print()
    
    print('='*70)
    print('DIAGNOSTIC COMPLETE')
    print('='*70)
    
except Exception as e:
    print(f'\n❌ ERROR: {e}')
    print('\nPossible issues:')
    print('  1. MongoDB is not running')
    print('  2. MONGODB_URI is incorrect')
    print('  3. Database name is wrong')
    print(f'\nCurrent MONGODB_URI: {mongodb_uri}')

