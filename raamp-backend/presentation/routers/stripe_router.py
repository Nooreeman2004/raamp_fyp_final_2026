import logging
import stripe
from fastapi import APIRouter, Depends, Header, Request, HTTPException
from pydantic import BaseModel

from presentation.routers.auth_router import get_current_user_email
from infrastructure.database.models.user_model import UserModel
from application.services.stripe_service import create_checkout_session, create_portal_session
from application.services.subscription_service import (
    update_user_subscription, 
    cancel_user_subscription, 
    mark_subscription_past_due
)
from config import Config


router = APIRouter(prefix="/stripe", tags=["stripe"])


class CheckoutRequest(BaseModel):
    plan: str


# ============================================
# CONTROLLER FUNCTIONS
# ============================================

async def create_checkout_session_controller(user_id: str, email: str, plan: str):
    """Create a Stripe checkout session"""
    try:
        session = create_checkout_session(user_id, email, plan)
        return {"url": session.url}
    except Exception as e:
        logging.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def create_portal_session_controller(customer_id: str):
    """Create a Stripe billing portal session"""
    if not customer_id:
        raise HTTPException(status_code=400, detail="No customer ID attached to user")
    try:
        session = create_portal_session(customer_id)
        return {"url": session.url}
    except Exception as e:
        logging.error(f"Stripe portal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_stripe_webhook_controller(event: dict):
    """Process Stripe webhook events"""
    event_type = event['type']
    event_id = event['id']
    
    # Handle initial checkout completion
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        
        metadata = session.get('metadata', {})
        user_id = metadata.get('userId')

        # Wallet top-up (one-time payment)
        if metadata.get('type') == 'wallet_topup':
            amount = float(metadata.get('amount', 0))
            if user_id and amount > 0:
                from infrastructure.repositories.wallet_repository import WalletRepository
                repo = WalletRepository()
                payment_intent_id = session.get('payment_intent', event_id)
                await repo.add_funds(
                    user_id=user_id,
                    amount=amount,
                    transaction_id=payment_intent_id
                )
                customer_id = session.get('customer')
                if customer_id:
                    user = await UserModel.find_one(UserModel.id == user_id)
                    if user and not user.stripeCustomerId:
                        user.stripeCustomerId = customer_id
                        await user.save()
                logging.info(f"Wallet topped up ${amount} for user {user_id}")
        else:
            # Subscription checkout
            plan = metadata.get('plan')
            customer_id = session.get('customer')
            subscription_id = session.get('subscription')
            
            if user_id and plan:
                success = await update_user_subscription(
                    user_id=user_id,
                    plan=plan,
                    customer_id=customer_id,
                    subscription_id=subscription_id,
                    status="active",
                    event_id=event_id
                )
                if not success:
                    logging.error(f"Failed to update subscription for {user_id}")
            else:
                logging.error("Missing metadata in stripe session")
    
    # Handle subscription updates (upgrades, downgrades, renewals)
    elif event_type == 'customer.subscription.updated':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')
        status = subscription.get('status')
        cancel_at_period_end = subscription.get('cancel_at_period_end', False)
        current_period_end = subscription.get('current_period_end')
        
        # Convert timestamp to datetime
        if current_period_end:
            from datetime import datetime
            current_period_end = datetime.fromtimestamp(current_period_end)
        
        # Determine plan from price
        plan_id = subscription['items']['data'][0]['price']['id'] if subscription.get('items') else None
        plan = _determine_plan_from_price_id(plan_id)
        
        # Find user by customer_id
        user = await UserModel.find_one(UserModel.stripeCustomerId == customer_id)
        if user:
            await update_user_subscription(
                user_id=str(user.id),
                plan=plan,
                subscription_id=subscription_id,
                status=status,
                current_period_end=current_period_end,
                cancel_at_period_end=cancel_at_period_end,
                event_id=event_id
            )
        else:
            logging.error(f"User not found for customer_id: {customer_id}")
    
    # Handle subscription deletion (immediate cancellation)
    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        
        # Find user by customer_id
        user = await UserModel.find_one(UserModel.stripeCustomerId == customer_id)
        if user:
            await cancel_user_subscription(user_id=str(user.id), event_id=event_id)
        else:
            logging.error(f"User not found for customer_id: {customer_id}")
    
    # Handle successful invoice payment (renewals)
    elif event_type == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')
        
        # Find user by customer_id
        user = await UserModel.find_one(UserModel.stripeCustomerId == customer_id)
        if user and user.subscriptionStatus == "past_due":
            # Reactivate subscription after successful payment
            await update_user_subscription(
                user_id=str(user.id),
                plan=user.subscriptionTier,
                subscription_id=subscription_id,
                status="active",
                event_id=event_id
            )
            logging.info(f"Subscription reactivated for user {user.id} after payment success")
    
    # Handle failed invoice payment
    elif event_type == 'invoice.payment_failed':
        invoice = event['data']['object']
        customer_id = invoice.get('customer')
        
        # Find user by customer_id
        user = await UserModel.find_one(UserModel.stripeCustomerId == customer_id)
        if user:
            await mark_subscription_past_due(user_id=str(user.id), event_id=event_id)
        else:
            logging.error(f"User not found for customer_id: {customer_id}")


def _determine_plan_from_price_id(price_id: str) -> str:
    """
    Determine plan tier from Stripe price ID.
    
    Note: Price IDs (price_xxx) are different from Product IDs (prod_xxx).
    To get price IDs:
    1. Go to Stripe Dashboard → Products
    2. Click on your product (Pro or Premium)
    3. Under "Pricing", copy the Price ID (starts with "price_")
    4. Add PRO_PRICE_ID and PREMIUM_PRICE_ID to your .env file
    """
    if not price_id:
        return "free"
    
    # Match against actual Stripe price IDs from config
    if price_id == Config.PRO_PRICE_ID:
        return "pro"
    elif price_id == Config.PREMIUM_PRICE_ID:
        return "premium"
    else:
        # Log unknown price ID for debugging
        logging.warning(f"Unknown price_id: {price_id}. Defaulting to 'free'. Add this to config if it's a valid subscription tier.")
        return "free"


# ============================================
# ROUTER ENDPOINTS
# ============================================

@router.post("/create-checkout-session")
async def create_checkout_session_endpoint(
    request_data: CheckoutRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    """Create a Stripe checkout session for a subscription plan"""
    user = await UserModel.find_one(UserModel.email == current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if request_data.plan not in ["pro", "premium"]:
        raise HTTPException(status_code=400, detail="Invalid plan selected")
        
    return await create_checkout_session_controller(str(user.id), user.email, request_data.plan)


@router.post("/create-portal-session")
async def create_portal_session_endpoint(
    current_user_email: str = Depends(get_current_user_email)
):
    """Create a Stripe billing portal session for subscription management"""
    user = await UserModel.find_one(UserModel.email == current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.stripeCustomerId:
        raise HTTPException(status_code=400, detail="No active subscription found to manage")

    return await create_portal_session_controller(user.stripeCustomerId)


@router.get("/invoices")
async def list_invoices_endpoint(
    current_user_email: str = Depends(get_current_user_email)
):
    """List Stripe invoices for the current user"""
    user = await UserModel.find_one(UserModel.email == current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.stripeCustomerId:
        return {"invoices": []}

    try:
        from application.services.stripe_service import list_customer_invoices
        result = list_customer_invoices(user.stripeCustomerId)
        return {"invoices": result}
    except Exception as e:
        logging.error("Error fetching invoices: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch invoices") from e


@router.post("/create-addfunds-session")
async def create_addfunds_session_endpoint(
    request_data: dict,
    current_user_email: str = Depends(get_current_user_email)
):
    """Create a Stripe checkout session for a one-time wallet top-up"""
    user = await UserModel.find_one(UserModel.email == current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    amount = request_data.get("amount")
    if not amount or not isinstance(amount, (int, float)) or amount <= 0 or amount > 10000:
        raise HTTPException(status_code=400, detail="Amount must be between $1 and $10,000")

    try:
        from application.services.stripe_service import create_addfunds_checkout_session
        session = create_addfunds_checkout_session(
            user_id=str(user.id),
            email=user.email,
            amount=amount,
            customer_id=user.stripeCustomerId
        )
        return {"url": session.url}
    except Exception as e:
        logging.error("Stripe add-funds checkout error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create checkout session") from e


@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """Handle Stripe webhook events"""
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, Config.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    await process_stripe_webhook_controller(event)
    return {"status": "success"}

