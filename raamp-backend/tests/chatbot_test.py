import asyncio
import os
import sys
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.abspath("."))

from infrastructure.database.database import connect_to_mongo, init_db
from infrastructure.database.models.business_model import BusinessModel
from infrastructure.database.models.chat_session_model import ChatSessionModel
from infrastructure.database.models.trend_ai_analysis_model import TrendAIAnalysisModel
from presentation.routers.chatbot_router import get_business_context, get_trend_context, get_generator

async def test_scenarios():
    print("🚀 Starting Intelligence & Awareness Test")
    print("=" * 60)
    
    await connect_to_mongo()
    await init_db()
    
    # 1. Fetch a real business for context
    business = await BusinessModel.find_one()
    if not business:
        print("⚠️ No business found in DB, creating a mock one for testing")
        business = BusinessModel(
            user_id="test@example.com",
            business_name="Green Bites Vegan Cafe",
            business_type="Restaurant",
            city="New York",
            specialties=["Organic Matcha", "Vegan Burgers", "Gluten-free Desserts"],
            description="A cozy vegan cafe focusing on organic ingredients and sustainable practices."
        )
        await business.insert()
    
    user_id = business.user_id
    print(f"✅ Using Business: {business.business_name} (User: {user_id})")
    
    # 2. Mock a trend analysis
    trend_analysis = await TrendAIAnalysisModel.find_one({"user_id": user_id})
    if not trend_analysis:
        print("⚠️ No trend analysis found, creating a mock one")
        trend_analysis = TrendAIAnalysisModel(
            trend_id="trend_123",
            user_id=user_id,
            trend_keyword="Sustainable Packaging",
            executive_summary="Users are increasingly demanding zero-plastic delivery options. High engagement for eco-friendly brands.",
            opportunity_window="Early Trend",
            status="completed"
        )
        await trend_analysis.insert()
    
    # 3. Create a session linked to this trend
    session_id = "test-session-123"
    session = await ChatSessionModel.find_one(ChatSessionModel.session_id == session_id)
    if session:
        await session.delete()
    
    session = ChatSessionModel(
        session_id=session_id,
        user_id=user_id,
        trend_ids=[trend_analysis.trend_id],
        messages=[]
    )
    await session.insert()
    print(f"✅ Created session {session_id} linked to trend {trend_analysis.trend_keyword}")
    
    # 4. Fetch Contexts
    print("\n📦 Fetching Contexts...")
    from application.services.rag.conversation_manager import get_conversation_manager
    manager = get_conversation_manager()
    biz_ctx = await get_business_context(user_id)
    trend_ctx = await get_trend_context(session_id, manager)
    
    print("-" * 20)
    print("Business Context Preview:")
    print(biz_ctx[:200] + "...")
    print("-" * 20)
    print("Trend Context Preview:")
    print(trend_ctx[:200] + "...")
    
    # 5. Run Inference
    generator = get_generator()
    
    scenarios = [
        "How can you help me today?",
        "What marketing strategy should I use for my specialties?",
        "Can you explain that sustainability trend we discussed and how it applies to my shop?",
        "What's the weather like for marketing tomorrow?" # Test "off-topic" query
    ]
    
    print("\n🤖 Running Scenario Tests...")
    for msg in scenarios:
        print(f"\n👤 User: {msg}")
        response = generator.chat(
            query=msg,
            business_context=biz_ctx,
            trend_context=trend_ctx,
            n_context=3
        )
        print(f"🤖 Assistant: {response['answer']}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(test_scenarios())
