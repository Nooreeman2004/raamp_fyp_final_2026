from typing import Optional
from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel


class InstagramRepository:
    async def find_by_user_id(self, user_id: str) -> Optional[InstagramConnectionModel]:
        return await InstagramConnectionModel.find_one(InstagramConnectionModel.user_id == user_id)

    async def create_or_update(self, user_id: str, ig_business_id: Optional[str] = None, username: Optional[str] = None, account_type: Optional[str] = None, linked_fb_page_id: Optional[str] = None, profile_picture_url: Optional[str] = None) -> InstagramConnectionModel:
        doc = await self.find_by_user_id(user_id)
        if not doc:
            doc = InstagramConnectionModel(user_id=user_id, ig_business_id=ig_business_id, username=username, account_type=account_type, linked_fb_page_id=linked_fb_page_id, profile_picture_url=profile_picture_url)
            await doc.insert()
            return doc
        if ig_business_id:
            doc.ig_business_id = ig_business_id
        if username:
            doc.username = username
        # preserve profile picture if provided
        if profile_picture_url:
            doc.profile_picture_url = profile_picture_url
        if account_type:
            doc.account_type = account_type
        if linked_fb_page_id:
            doc.linked_fb_page_id = linked_fb_page_id
        doc.updated_at = __import__('datetime').datetime.utcnow()
        # allow optional profile_picture_url passed via kwargs
        # if caller provided profile_picture_url attribute on doc assignment, it'll be saved
        await doc.save()
        return doc
