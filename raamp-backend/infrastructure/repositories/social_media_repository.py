from typing import Optional, List
from infrastructure.database.models.social_media_account_model import SocialMediaAccountModel
from infrastructure.database.models.user_model import UserModel


class SocialMediaRepository:
    async def find_by_user_id(self, user_id: str) -> Optional[SocialMediaAccountModel]:
        return await SocialMediaAccountModel.find_one(SocialMediaAccountModel.user_id == user_id)

    async def create_or_update(self, user_id: str, fb_long_lived_token: str = None, page_id: str = None, page_name: str = None, page_access_token: str = None, ig_business_id: str = None, expires_at=None) -> SocialMediaAccountModel:
        doc = await self.find_by_user_id(user_id)
        if not doc:
            doc = SocialMediaAccountModel(
                user_id=user_id,
                fb_long_lived_token=fb_long_lived_token,
                page_id=page_id,
                page_name=page_name,
                page_access_token=page_access_token,
                ig_business_id=ig_business_id,
                expires_at=expires_at
            )
            await doc.insert()
            return doc
        if fb_long_lived_token is not None:
            doc.fb_long_lived_token = fb_long_lived_token
        if page_id is not None:
            doc.page_id = page_id
        if page_name is not None:
            doc.page_name = page_name
        if page_access_token is not None:
            doc.page_access_token = page_access_token
        if ig_business_id is not None:
            doc.ig_business_id = ig_business_id
        if expires_at is not None:
            doc.expires_at = expires_at
        doc.updated_at = __import__('datetime').datetime.utcnow()
        await doc.save()
        return doc

    async def delete_by_user_id(self, user_id: str) -> bool:
        doc = await self.find_by_user_id(user_id)
        if not doc:
            return False
        await doc.delete()
        return True
    
    async def get_admin_users(self) -> List[UserModel]:
        """Get all admin users for system notifications"""
        # For now, return users with admin role or specific email domain
        # Adjust this based on your actual admin identification logic
        admin_users = await UserModel.find(
            UserModel.role == "admin"
        ).to_list()
        
        # If no admin role exists, you can filter by email or other criteria
        if not admin_users:
            admin_users = await UserModel.find().limit(1).to_list()  # Fallback to first user
        
        return admin_users
