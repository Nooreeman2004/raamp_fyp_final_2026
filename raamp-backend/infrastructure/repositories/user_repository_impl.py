# Infrastructure Layer - User Repository Implementation (MongoDB)
from typing import Optional
from datetime import datetime
from bson import ObjectId
from domain.entities.user import User
from domain.repositories.user_repository import IUserRepository
from infrastructure.database.models.user_model import UserModel


class UserRepository(IUserRepository):
    """Concrete implementation of User repository using MongoDB/Beanie"""
    
    def _to_entity(self, model: UserModel) -> User:
        """Convert MongoDB document to domain entity"""
        return User(
            id=str(model.id),  # MongoDB uses ObjectId, convert to string
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            agreed_to_terms=model.agreed_to_terms,
            is_verified=model.is_verified,
            verification_code=model.verification_code,
            code_expires_at=model.code_expires_at,
            code_sent_at=model.code_sent_at,
            first_name=model.first_name,
            last_name=model.last_name,
            phone_number=model.phone_number,
            company=model.company,
            role=model.role,
            bio=model.bio,
            business_domain=model.business_domain,
            profile_completed=model.profile_completed,
            profile_picture=model.profile_picture,
            is_admin=model.is_admin,
            subscription=model.subscription,
            last_login=model.last_login,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        user_model = await UserModel.find_one(UserModel.email == email.lower())
        return self._to_entity(user_model) if user_model else None
    
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        user_model = await UserModel.find_one(UserModel.username == username)
        return self._to_entity(user_model) if user_model else None
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if email already exists"""
        count = await UserModel.find(UserModel.email == email.lower()).count()
        return count > 0
    
    async def exists_by_username(self, username: str) -> bool:
        """Check if username already exists"""
        count = await UserModel.find(UserModel.username == username).count()
        return count > 0
    
    async def create(self, user: User) -> User:
        """Create new user"""
        # Use profile_picture from user if provided, otherwise use default Pixabay placeholder
        profile_picture = user.profile_picture or "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_960_720.png"
        
        user_model = UserModel(
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            agreed_to_terms=user.agreed_to_terms,
            is_verified=user.is_verified,
            verification_code=user.verification_code,
            code_expires_at=user.code_expires_at,
            code_sent_at=user.code_sent_at,
            profile_picture=profile_picture,
            is_admin=False,
            subscription={"type": "free", "credits": 5},
            last_login=datetime.utcnow(),
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        await user_model.insert()
        return self._to_entity(user_model)
    
    async def verify_user(self, email: str) -> bool:
        """Mark user as verified and clear verification code"""
        user_model = await UserModel.find_one(UserModel.email == email.lower())
        if not user_model:
            return False
        
        user_model.is_verified = True
        user_model.verification_code = None
        user_model.code_expires_at = None
        user_model.updated_at = datetime.utcnow()
        await user_model.save()
        return True
    
    async def update_verification_code(
        self, 
        email: str, 
        code: str, 
        expires_at: datetime,
        sent_at: datetime
    ) -> bool:
        """Update user's verification code"""
        user_model = await UserModel.find_one(UserModel.email == email.lower())
        if not user_model:
            return False
        
        user_model.verification_code = code
        user_model.code_expires_at = expires_at
        user_model.code_sent_at = sent_at
        user_model.updated_at = datetime.utcnow()
        await user_model.save()
        return True
    
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
        """Update user profile - all fields are required"""
        user_model = await UserModel.find_one(UserModel.email == email.lower())
        if not user_model:
            return None
        
        user_model.first_name = first_name
        user_model.last_name = last_name
        user_model.phone_number = phone_number
        user_model.company = company
        user_model.role = role
        user_model.bio = bio
        user_model.business_domain = business_domain
        user_model.profile_completed = True
        
        user_model.updated_at = datetime.utcnow()
        await user_model.save()
        return self._to_entity(user_model)

    async def update_connection_flags(self, email: str, facebook: bool = None, instagram: bool = None, google_maps: bool = None) -> bool:
        """Update per-user connection flags (facebook/instagram/google_maps)"""
        user_model = await UserModel.find_one(UserModel.email == email.lower())
        if not user_model:
            return False
        if facebook is not None:
            user_model.facebook_connected = facebook
        if instagram is not None:
            user_model.instagram_connected = instagram
        if google_maps is not None:
            user_model.google_maps_connected = google_maps
        user_model.updated_at = datetime.utcnow()
        await user_model.save()
        return True

    async def update_google_place_details(self, email: str, place_id: str = None, name: str = None, address: str = None, latitude: float = None, longitude: float = None) -> bool:
        """Update user's stored Google Maps place details"""
        user_model = await UserModel.find_one(UserModel.email == email.lower())
        if not user_model:
            return False
        if place_id is not None:
            user_model.google_place_id = place_id
        if name is not None:
            user_model.google_place_name = name
        if address is not None:
            user_model.google_place_address = address
        if latitude is not None:
            user_model.google_lat = latitude
        if longitude is not None:
            user_model.google_lng = longitude
        user_model.updated_at = datetime.utcnow()
        await user_model.save()
        return True

    async def update_profile_completed(self, email: str, completed: bool = True) -> bool:
        user_model = await UserModel.find_one(UserModel.email == email.lower())
        if not user_model:
            return False
        user_model.profile_completed = completed
        user_model.updated_at = datetime.utcnow()
        await user_model.save()
        return True

    async def get_profile_summary(self, email: str) -> Optional[dict]:
        user_model = await UserModel.find_one(UserModel.email == email.lower())
        if not user_model:
            return None
        return {
            "email": user_model.email,
            "first_name": user_model.first_name,
            "last_name": user_model.last_name,
            "phone_number": user_model.phone_number,
            "company": user_model.company,
            "role": user_model.role,
            "bio": user_model.bio,
            "business_domain": user_model.business_domain,
            "profile_picture": user_model.profile_picture,
            "profile_completed": user_model.profile_completed,
            "facebook_connected": getattr(user_model, 'facebook_connected', False),
            "instagram_connected": getattr(user_model, 'instagram_connected', False),
            "google_maps_connected": getattr(user_model, 'google_maps_connected', False),
        }
    
    async def update_last_login(self, email: str) -> bool:
        """Update user's last login timestamp"""
        user_model = await UserModel.find_one(UserModel.email == email.lower())
        if not user_model:
            return False
        
        user_model.last_login = datetime.utcnow()
        user_model.updated_at = datetime.utcnow()
        await user_model.save()
        return True

    async def update_password(self, email: str, new_password_hash: str) -> bool:
        """Update user's password hash"""
        user_model = await UserModel.find_one(UserModel.email == email.lower())
        if not user_model:
            return False

        user_model.password_hash = new_password_hash
        user_model.updated_at = datetime.utcnow()
        await user_model.save()
        return True

