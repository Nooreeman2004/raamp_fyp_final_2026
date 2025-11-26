# Domain Layer - User Repository Interface
from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.user import User


class IUserRepository(ABC):
    """Repository interface - defines contract without implementation details"""
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        pass
    
    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        pass
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """Create new user"""
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if email already exists"""
        pass
    
    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if username already exists"""
        pass
    
    @abstractmethod
    async def update_profile(
        self,
        email: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        company: str,
        role: str,
        bio: str,
        business_domain: str
    ) -> Optional[User]:
        """Update user profile - all fields required"""
        pass
    
    @abstractmethod
    async def update_last_login(self, email: str) -> bool:
        """Update user's last login timestamp"""
        pass
