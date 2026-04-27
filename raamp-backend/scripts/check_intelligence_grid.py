import sys
import asyncio
from infrastructure.database.models.trend_ai_analysis_model import TrendAIAnalysisModel
from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from infrastructure.database.database import init_db
import os

async def check_intelligence_grid():
    # Initialize database
    await init_db()
    
    print('='*60)
    print('INTELLIGENCE GRID DIAGNOSTIC')
    print('='*60)
    
    # Check for recent trend detections
    print('\n1. Checking recent trend detections...')
    recent_trends = await TrendDetectionModel.find().sort('-detected_at').limit(5).to_list()
    
    if not recent_trends:
        print('   ❌ NO TREND DETECTIONS FOUND IN DATABASE')
        print('   Root cause: No trends have been detected yet')
        return
    
    print(f'   ✅ Found {len(recent_trends)} recent trends')
    for i, trend in enumerate(recent_trends[:3]):
        print(f'   - Trend {i+1}: {trend.keyword} (niche: {trend.niche}, signal_id: {trend.trend_signal_id})')
    
    # Check AI analysis for these trends
    print('\n2. Checking AI Analysis status...')
    trend_signal_ids = [str(t.trend_signal_id) for t in recent_trends if t.trend_signal_id]
    
    if not trend_signal_ids:
        print('   ❌ NO TREND SIGNAL IDs FOUND')
        print('   Root cause: Trends exist but have no trend_signal_id')
        return
    
    ai_analyses = await TrendAIAnalysisModel.find({'trend_id': {'$in': trend_signal_ids}}).to_list()
    
    if not ai_analyses:
        print('   ❌ NO AI ANALYSIS RECORDS FOUND')
        print('   Root cause: AI analysis has never been triggered for these trends')
        print('   Solution: The frontend should call /api/trends/{trend_id}/ai-analysis to trigger generation')
        return
    
    print(f'   ✅ Found {len(ai_analyses)} AI analysis records')
    
    # Check each analysis
    for analysis in ai_analyses:
        print(f'\n   Analysis for trend_id: {analysis.trend_id}')
        print(f'   - Status: {analysis.status}')
        print(f'   - Keyword: {analysis.trend_keyword}')
        
        if analysis.status == 'pending':
            print('   ⏳ Status: PENDING - AI generation in progress')
            
        elif analysis.status == 'failed':
            print(f'   ❌ Status: FAILED')
            print(f'   - Error: {analysis.error_message}')
            print('   Root cause: AI generation failed')
            
        elif analysis.status == 'completed':
            print('   ✅ Status: COMPLETED')
            
            # Check campaign_ideas
            campaign_ideas = analysis.campaign_ideas or []
            print(f'   - Campaign Ideas: {len(campaign_ideas)} items')
            if campaign_ideas:
                print(f'     First idea: {campaign_ideas[0].get("title", "N/A")}')
            else:
                print('     ⚠️  Campaign ideas array is EMPTY')
            
            # Check growth_hacks
            growth_hacks = analysis.growth_hacks or []
            print(f'   - Growth Hacks: {len(growth_hacks)} items')
            if growth_hacks:
                print(f'     First hack: {growth_hacks[0][:50]}...')
            else:
                print('     ⚠️  Growth hacks array is EMPTY')
            
            if not campaign_ideas and not growth_hacks:
                print('\n   🔍 ROOT CAUSE: AI returned empty arrays')
                print('   - The LLM generated a response but campaign_ideas and growth_hacks are empty')
                print('   - This could be due to:')
                print('     1. LLM prompt not being followed correctly')
                print('     2. JSON parsing issue')
                print('     3. LLM returning null/empty for these fields')
        else:
            print(f'   ⚠️  Unknown status: {analysis.status}')
    
    # Check API keys
    print('\n3. Checking API Keys...')
    gemini_key = os.getenv('GEMINI_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if gemini_key:
        print(f'   ✅ GEMINI_API_KEY: Set ({gemini_key[:10]}...)')
    else:
        print('   ❌ GEMINI_API_KEY: NOT SET')
    
    if openai_key:
        print(f'   ✅ OPENAI_API_KEY: Set ({openai_key[:10]}...)')
    else:
        print('   ⚠️  OPENAI_API_KEY: NOT SET')
    
    if not gemini_key and not openai_key:
        print('\n   🔍 ROOT CAUSE: No AI API keys configured')
        print('   Solution: Set GEMINI_API_KEY or OPENAI_API_KEY in .env file')
    
    print('\n' + '='*60)
    print('DIAGNOSTIC COMPLETE')
    print('='*60)

if __name__ == '__main__':
    asyncio.run(check_intelligence_grid())
