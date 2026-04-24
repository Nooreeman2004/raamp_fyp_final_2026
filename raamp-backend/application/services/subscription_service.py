from datetime import datetime, timedelta
import logging
from infrastructure.database.models.user_model import UserModel
from application.services.mailtrap_service import MailtrapService
from beanie import PydanticObjectId
from config import Config

mailtrap_service = MailtrapService()


async def update_user_subscription(
    user_id: str, 
    plan: str, 
    customer_id: str = None, 
    subscription_id: str = None,
    status: str = "active",
    current_period_end: datetime = None,
    cancel_at_period_end: bool = False,
    event_id: str = None
):
    """
    Update a user's subscription plan and credits.
    
    Args:
        user_id: The user's ID
        plan: The subscription plan ('pro', 'premium', or 'free')
        customer_id: The Stripe customer ID (optional)
        subscription_id: The Stripe subscription ID (optional)
        status: Subscription status (active, canceled, past_due)
        current_period_end: End of current billing period
        cancel_at_period_end: Whether subscription is set to cancel
        event_id: The Stripe event ID (optional, for idempotency)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        user = await UserModel.get(PydanticObjectId(user_id))
        if not user:
            logging.error(f"User not found for id: {user_id}")
            return False

        # DEMO USER PROTECTION: Never modify demo user's subscription via webhooks
        if user.email.lower() == "abdullah@gmail.com":
            logging.warning(f"🛡️ DEMO PROTECTION: Ignoring subscription update for demo user {user.email}")
            return True

        # Check if event was already processed (idempotency)
        if event_id and user.processed_stripe_events and event_id in user.processed_stripe_events:
            logging.info(f"Stripe event {event_id} already processed for user {user_id}. Skipping.")
            return True

        now = datetime.utcnow()
        
        # Update subscription based on plan
        if plan == "pro":
            user.subscriptionTier = "pro"
            user.adCreditsRemaining = 50
            if not current_period_end:
                user.subscriptionEndDate = now + timedelta(days=30)
        elif plan == "premium":
            user.subscriptionTier = "premium"
            user.adCreditsRemaining = -1  # -1 represents unlimited
            if not current_period_end:
                user.subscriptionEndDate = now + timedelta(days=30)
        elif plan == "free":
            user.subscriptionTier = "free"
            user.adCreditsRemaining = 5
            user.subscriptionEndDate = None

        # Update Stripe metadata
        if customer_id:
            user.stripeCustomerId = customer_id
        
        if subscription_id:
            user.stripeSubscriptionId = subscription_id
        
        # Update subscription status
        user.subscriptionStatus = status
        user.cancelAtPeriodEnd = cancel_at_period_end
        
        # Set billing period end if provided
        if current_period_end:
            user.currentPeriodEnd = current_period_end
            user.subscriptionEndDate = current_period_end
            
        # Track processed event for idempotency
        if event_id:
            if not user.processed_stripe_events:
                user.processed_stripe_events = []
            user.processed_stripe_events.append(event_id)

        await user.save()
        
        # Send upgrade email
        if user.email and plan in ["pro", "premium"] and status == "active":
            name = user.first_name if user.first_name else user.username
            await mailtrap_service.send_upgrade_email(to_email=user.email, name=name, plan=plan)
            
        logging.info(f"Successfully updated subscription for user {user_id} to {plan} (status: {status})")
        return True
        
    except Exception as e:
        logging.error(f"Failed to update subscription for user {user_id}: {str(e)}")
        return False


async def cancel_user_subscription(user_id: str, event_id: str = None):
    """
    Cancel a user's subscription (downgrade to free).
    
    Args:
        user_id: The user's ID
        event_id: The Stripe event ID (optional, for idempotency)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        user = await UserModel.get(PydanticObjectId(user_id))
        if not user:
            logging.error(f"User not found for id: {user_id}")
            return False

        # DEMO USER PROTECTION: Never cancel demo user's subscription
        if user.email.lower() == "abdullah@gmail.com":
            logging.warning(f"🛡️ DEMO PROTECTION: Ignoring cancellation for demo user {user.email}")
            return True

        # Check if event was already processed
        if event_id and user.processed_stripe_events and event_id in user.processed_stripe_events:
            logging.info(f"Stripe event {event_id} already processed for user {user_id}. Skipping.")
            return True

        # Downgrade to free tier
        user.subscriptionTier = "free"
        user.adCreditsRemaining = 5
        user.subscriptionStatus = "canceled"
        user.subscriptionEndDate = None
        user.cancelAtPeriodEnd = False
        user.currentPeriodEnd = None
        
        # Track processed event
        if event_id:
            if not user.processed_stripe_events:
                user.processed_stripe_events = []
            user.processed_stripe_events.append(event_id)

        await user.save()
        
        logging.info(f"Successfully canceled subscription for user {user_id}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to cancel subscription for user {user_id}: {str(e)}")
        return False


async def mark_subscription_past_due(user_id: str, event_id: str = None):
    """
    Mark a user's subscription as past due after payment failure.
    
    Args:
        user_id: The user's ID
        event_id: The Stripe event ID (optional, for idempotency)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # DEMO USER PROTECTION: Never mark demo user as past due
        if user.email.lower() == "abdullah@gmail.com":
            logging.warning(f"🛡️ DEMO PROTECTION: Ignoring past_due status for demo user {user.email}")
            return True

        # er = await UserModel.get(PydanticObjectId(user_id))
        if not user:
            logging.error(f"User not found for id: {user_id}")
            return False

        # Check if event was already processed
        if event_id and user.processed_stripe_events and event_id in user.processed_stripe_events:
            logging.info(f"Stripe event {event_id} already processed for user {user_id}. Skipping.")
            return True

        # Mark as past due
        user.subscriptionStatus = "past_due"
        
        # Track processed event
        if event_id:
            if not user.processed_stripe_events:
                user.processed_stripe_events = []
            user.processed_stripe_events.append(event_id)

        await user.save()
        
        # Send payment failure notification
        if user.email:
            name = user.first_name if user.first_name else user.username
            # Create billing portal URL for user to update payment method
            portal_url = f"{Config.FRONTEND_URL}/dashboard/billing"
            await mailtrap_service.send_payment_failed_email(
                to_email=user.email, 
                name=name, 
                portal_url=portal_url
            )
            logging.info(f"Payment failure email sent to {user.email}")
        
        logging.info(f"Marked subscription as past_due for user {user_id}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to mark subscription past_due for user {user_id}: {str(e)}")
        return False

