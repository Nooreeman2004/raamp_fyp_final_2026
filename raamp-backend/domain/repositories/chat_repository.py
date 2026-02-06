from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from datetime import datetime

class IChatRepository(ABC):
    """Interface for Chat Repository"""
    
    @abstractmethod
    async def create_session(self, session_id: str, user_id: Optional[str] = None) -> Dict:
        pass
        
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    async def add_message(self, session_id: str, role: str, content: str) -> Optional[Dict]:
        pass
        
    @abstractmethod
    async def get_history(self, session_id: str, limit: int = None) -> List[Dict]:
        pass
        
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        pass
        
    @abstractmethod
    async def clear_history(self, session_id: str) -> bool:
        pass
