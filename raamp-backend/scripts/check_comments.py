"""Check comment analysis database records"""
import asyncio
from infrastructure.database.database import connect_to_mongo, init_db
from infrastructure.database.models.comment_analysis_model import CommentAnalysisModel

async def check():
    await connect_to_mongo()
    await init_db()
    
    count = await CommentAnalysisModel.count()
    print(f'Total comments in DB: {count}')
    
    if count > 0:
        sample = await CommentAnalysisModel.find_all().limit(3).to_list()
        print('Sample comments:')
        for c in sample:
            print(f'  - {c.text[:50]}... (spam: {c.is_spam}, sentiment: {c.sentiment})')
    else:
        print('\n⚠️ No comments found in database!')
        print('Comments will be added when:')
        print('  1. Instagram/Facebook webhooks deliver comment events')
        print('  2. They are processed by the comment analysis service')
        print('\nThe "not found" error is expected when no comments have been analyzed yet.')

if __name__ == "__main__":
    asyncio.run(check())
