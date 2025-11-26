from typing import Optional
from datetime import datetime
from infrastructure.database.models.oauth_state_model import OAuthStateModel


class OAuthStateRepository:
    async def create_state(self, user_id: str, state: str, expires_at: Optional[datetime] = None) -> OAuthStateModel:
        doc = OAuthStateModel(user_id=user_id, state=state)
        if expires_at:
            doc.expires_at = expires_at
        await doc.insert()
        return doc

    async def validate_and_consume(self, user_id: str, state: str) -> bool:
        now = datetime.utcnow()
        doc = await OAuthStateModel.find_one((OAuthStateModel.user_id == user_id) & (OAuthStateModel.state == state))
        if not doc:
            return False
        if doc.expires_at < now:
            await doc.delete()
            return False
        # consume
        await doc.delete()
        return True

    async def validate_and_consume_by_state(self, state: str) -> Optional[str]:
        """Validate an OAuth state token and return the associated user_id (consuming the state).

        Useful when the callback cannot rely on an authenticated cookie and must resolve the user
        purely via the provided state token.
        Returns the user_id (email) if valid, otherwise None.
        """
        now = datetime.utcnow()
        doc = await OAuthStateModel.find_one(OAuthStateModel.state == state)
        if not doc:
            return None
        if doc.expires_at < now:
            await doc.delete()
            return None
        user_id = doc.user_id
        # consume
        await doc.delete()
        return user_id
