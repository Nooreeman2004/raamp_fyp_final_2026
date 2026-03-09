import stripe
from config import Config

stripe.api_key = Config.STRIPE_SECRET_KEY

def create_checkout_session(user_id: str, email: str, plan: str):
    """
    Create a Stripe checkout session for subscription purchase.
    
    Args:
        user_id: The user's ID
        email: The user's email
        plan: The subscription plan ('pro' or 'premium')
        
    Returns:
        Stripe checkout session object
    """
    if plan == "pro":
        product_id = Config.PRO_PRODUCT_ID
        unit_amount = 1000  # $10.00
    elif plan == "premium":
        product_id = Config.PREMIUM_PRODUCT_ID
        unit_amount = 2500  # $25.00
    else:
        raise ValueError("Invalid plan")

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        customer_email=email,
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product': product_id,
                'recurring': {'interval': 'month'},
                'unit_amount': unit_amount,
            },
            'quantity': 1,
        }],
        mode='subscription',
        success_url=f"{Config.FRONTEND_URL}/dashboard/billing?success=true",
        cancel_url=f"{Config.FRONTEND_URL}/pricing?canceled=true",
        metadata={
            "userId": user_id,
            "plan": plan
        }
    )
    return session


def create_portal_session(customer_id: str):
    """
    Create a Stripe billing portal session for subscription management.
    
    Args:
        customer_id: The Stripe customer ID
        
    Returns:
        Stripe portal session object
    """
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{Config.FRONTEND_URL}/dashboard/billing"
    )
    return session
