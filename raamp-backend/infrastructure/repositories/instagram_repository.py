from datetime import datetime
from typing import Optional
from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel


class InstagramRepository:
    async def find_by_user_id(self, user_id: str) -> Optional[InstagramConnectionModel]:
        return await InstagramConnectionModel.find_one(InstagramConnectionModel.user_id == user_id)

    async def create_or_update(self, user_id: str, ig_business_id: Optional[str] = None, page_access_token: Optional[str] = None, user_access_token: Optional[str] = None, username: Optional[str] = None, account_type: Optional[str] = None, linked_fb_page_id: Optional[str] = None, profile_picture_url: Optional[str] = None, expires_at: Optional[datetime] = None) -> InstagramConnectionModel:
        doc = await self.find_by_user_id(user_id)
        if not doc:
            doc = InstagramConnectionModel(
                user_id=user_id, 
                ig_business_id=ig_business_id, 
                page_access_token=page_access_token, 
                user_access_token=user_access_token,
                username=username, 
                account_type=account_type, 
                linked_fb_page_id=linked_fb_page_id, 
                profile_picture_url=profile_picture_url,
                expires_at=expires_at,
                last_refreshed_at=datetime.utcnow()
            )
            await doc.insert()
            return doc
        if ig_business_id:
            doc.ig_business_id = ig_business_id
        if page_access_token:
            doc.page_access_token = page_access_token
        if user_access_token:
            doc.user_access_token = user_access_token
        if username:
            doc.username = username
        # preserve profile picture if provided
        if profile_picture_url:
            doc.profile_picture_url = profile_picture_url
        if account_type:
            doc.account_type = account_type
        if linked_fb_page_id:
            doc.linked_fb_page_id = linked_fb_page_id
        if expires_at:
            doc.expires_at = expires_at
        
        doc.token_valid = True  # Reset on manual update
        doc.updated_at = datetime.utcnow()
        # allow optional profile_picture_url passed via kwargs
        # if caller provided profile_picture_url attribute on doc assignment, it'll be saved
        await doc.save()
        return doc

    async def delete_by_user_id(self, user_id: str) -> bool:
        """Delete the Instagram connection document for the given user_id."""
        doc = await self.find_by_user_id(user_id)
        if doc:
            await doc.delete()
            return True
        return False

    async def get_all_connections(self) -> list[InstagramConnectionModel]:
        """Retrieve all Instagram connections for background processing."""
        return await InstagramConnectionModel.find_all().to_list()
