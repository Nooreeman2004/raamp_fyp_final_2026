from typing import Optional
from infrastructure.database.models.facebook_connection_model import FacebookConnectionModel


class FacebookRepository:
    async def find_by_user_id(self, user_id: str) -> Optional[FacebookConnectionModel]:
        return await FacebookConnectionModel.find_one(FacebookConnectionModel.user_id == user_id)
    
    async def get_connection_by_user_id(self, user_id: str) -> Optional[FacebookConnectionModel]:
        """Alias for find_by_user_id for compatibility with use cases"""
        return await self.find_by_user_id(user_id)

    async def create_or_update(
        self,
        user_id: str,
        access_token: str,
        fb_user_id: Optional[str] = None,
        fb_pages: Optional[list] = None,
        granted_scopes: Optional[list] = None,
        ad_accounts: Optional[list] = None,
        selected_ad_account_id: Optional[str] = None,
    ) -> FacebookConnectionModel:
        doc = await self.find_by_user_id(user_id)
        if not doc:
            doc = FacebookConnectionModel(
                user_id=user_id,
                access_token=access_token,
                fb_user_id=fb_user_id or None,
                fb_pages=fb_pages or [],
                granted_scopes=granted_scopes or [],
                ad_accounts=ad_accounts or [],
                selected_ad_account_id=selected_ad_account_id,
            )
            await doc.insert()
            return doc
        doc.access_token = access_token
        if fb_user_id:
            doc.fb_user_id = fb_user_id
        if fb_pages is not None:
            doc.fb_pages = fb_pages
        if granted_scopes is not None:
            doc.granted_scopes = granted_scopes
        if ad_accounts is not None:
            doc.ad_accounts = ad_accounts
        if selected_ad_account_id is not None:
            doc.selected_ad_account_id = selected_ad_account_id
        doc.updated_at = __import__('datetime').datetime.utcnow()
        await doc.save()
        return doc

    async def delete_by_user_id(self, user_id: str) -> bool:
        """Delete the Facebook connection document for the given user_id."""
        doc = await self.find_by_user_id(user_id)
        if not doc:
            return False
        await doc.delete()
        return True
