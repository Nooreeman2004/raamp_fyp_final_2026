"""
Credit Service
==============
Handles usage enforcement, credit deduction, and tier-based limits for RAAMP.
Ensures that users are charged 'ad credits' for AI-powered actions.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from pydantic import BaseModel

from infrastructure.database.models.user_model import UserModel
from infrastructure.repositories.wallet_repository import WalletRepository

logger = logging.getLogger(__name__)

# Action cost matrix
ACTION_COSTS = {
    "caption_generation": 1,
    "geo_radar_scan": 2,
    "campaign_brief": 3,
    "advanced_strategy": 5,
    "image_generation": 2,
    "video_generation": 10
}

class CreditTransaction(BaseModel):
    user_id: str
    action_type: str
    credits_consumed: int
    timestamp: datetime
    remaining_balance: int

class CreditService:
    """Service to manage and enforce ad credits based on user tiers."""

    def __init__(self):
        self.wallet_repo = WalletRepository()

    async def check_and_deduct(self, user_id: str, action_type: str) -> bool:
        """
        Check if user has enough credits for the action and deduct if successful.
        
        Args:
            user_id: User email/ID
            action_type: Type of action from ACTION_COSTS
            
        Returns:
            True if authorized and deducted
            
        Raises:
            HTTPException: 402 Payment Required if credits are insufficient
        """
        user = await UserModel.find_one(UserModel.email == user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 0. DEMO OVERRIDE: Premium status for demo user
        if user_id.lower() == "abdullah@gmail.com":
            logger.info(f"✨ DEMO BYPASS: User {user_id} automatically granted Premium status.")
            return True

        # 1. Monthly Reset for Free Users (Checks if reset is needed)
        await self._ensure_monthly_reset(user)

        # 2. Premium Users have unlimited access
        if user.subscriptionTier == "premium":
            logger.info(f"✨ Premium User {user_id}: Unlimited access granted for {action_type}")
            return True

        # 3. Determine Cost
        cost = ACTION_COSTS.get(action_type, 1)
        
        # 4. Check Credits
        current_credits = user.adCreditsRemaining
        if current_credits < cost:
            logger.warning(f"🚫 User {user_id} ({user.subscriptionTier}): Insufficient credits for {action_type}. Needed: {cost}, Has: {current_credits}")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient ad credits. Required: {cost}, Available: {current_credits}. Please upgrade or add funds."
            )

        # 5. Deduct Credits
        user.adCreditsRemaining -= cost
        user.updated_at = datetime.utcnow()
        await user.save()

        # 6. Log Transaction (Simple log for now, could be a database collection)
        logger.info(f"💳 CREDIT DEDUCTED: User={user_id} | Action={action_type} | Consumed={cost} | Remaining={user.adCreditsRemaining}")
        
        # Optional: We could save this to a 'credit_transactions' collection here
        
        return True

    async def _ensure_monthly_reset(self, user: UserModel):
        """
        Ensures Free users get 100 credits on the 1st of the month.
        Checks 'updated_at' or a specific 'last_reset_date' to avoid double resets.
        """
        # Skip for demo user
        if user.email.lower() == "abdullah@gmail.com":
            return

        if user.subscriptionTier != "free":
            return

        now = datetime.utcnow()
        
        # Check if the user has already received their credits for THIS month
        # We'll use a field 'last_credit_reset_at' if it exists, otherwise assume based on current month
        last_reset = getattr(user, "last_credit_reset_at", None)
        
        should_reset = False
        if not last_reset:
            should_reset = True
        elif last_reset.month != now.month or last_reset.year != now.year:
            should_reset = True

        if should_reset:
            logger.info(f"🔄 Monthly Reset for Free User {user.email}: Granting 100 credits")
            user.adCreditsRemaining = 100
            user.last_credit_reset_at = now
            await user.save()

    def get_action_cost(self, action_type: str) -> int:
        """Get the cost for a specific action"""
        return ACTION_COSTS.get(action_type, 1)

# Singleton helper
_credit_service = None

def get_credit_service() -> CreditService:
    global _credit_service
    if _credit_service is None:
        _credit_service = CreditService()
    return _credit_service
