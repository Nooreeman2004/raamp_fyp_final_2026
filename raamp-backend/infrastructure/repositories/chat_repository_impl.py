from typing import Optional, List, Dict
from datetime import datetime
from domain.repositories.chat_repository import IChatRepository
from infrastructure.database.models.chat_session_model import ChatSessionModel

class ChatRepository(IChatRepository):
    """MongoDB Implementation of Chat Repository"""
    
    async def create_session(self, session_id: str, user_id: Optional[str] = None) -> Dict:
        """Create a new chat session"""
        session = ChatSessionModel(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            last_activity=datetime.utcnow()
        )
        await session.insert()
        return session.dict()
        
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        session = await ChatSessionModel.find_one(ChatSessionModel.session_id == session_id)
        return session.dict() if session else None

    async def add_message(self, session_id: str, role: str, content: str) -> Optional[Dict]:
        """Add a message to the session"""
        session = await ChatSessionModel.find_one(ChatSessionModel.session_id == session_id)
        if not session:
            # Auto-create if not exists (for robustness)
            session = ChatSessionModel(session_id=session_id, messages=[])
            await session.insert()
            
        new_msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        
        session.messages.append(new_msg)
        session.last_activity = datetime.utcnow()
        await session.save()
        return session.dict()
        
    async def get_history(self, session_id: str, limit: int = None) -> List[Dict]:
        """Get message history"""
        session = await ChatSessionModel.find_one(ChatSessionModel.session_id == session_id)
        if not session:
            return []
            
        messages = session.messages
        if limit and limit > 0:
            messages = messages[-limit:]
            
        return messages
        
    async def delete_session(self, session_id: str) -> bool:
        """Delete exact session"""
        session = await ChatSessionModel.find_one(ChatSessionModel.session_id == session_id)
        if session:
            await session.delete()
            return True
        return False
        
    async def clear_history(self, session_id: str) -> bool:
        """Clear messages but keep session"""
        session = await ChatSessionModel.find_one(ChatSessionModel.session_id == session_id)
        if session:
            session.messages = []
            session.last_activity = datetime.utcnow()
            await session.save()
            return True
        return False

    async def link_trend(self, session_id: str, trend_id: str) -> bool:
        """Link a trend ID to the session"""
        session = await ChatSessionModel.find_one(ChatSessionModel.session_id == session_id)
        if session:
            if not hasattr(session, 'trend_ids'):
                session.trend_ids = []
            if trend_id not in session.trend_ids:
                session.trend_ids.append(trend_id)
                session.last_activity = datetime.utcnow()
                await session.save()
            return True
        return False
