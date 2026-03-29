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
    """
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{Config.FRONTEND_URL}/dashboard/billing"
    )
    return session


def list_customer_invoices(customer_id: str, limit: int = 20):
    """
    List Stripe invoices for a specific customer.
    """
    invoices = stripe.Invoice.list(
        customer=customer_id,
        limit=limit,
        expand=["data.charge"]
    )
    
    result = []
    for inv in invoices.data:
        result.append({
            "id": inv.id,
            "date": inv.created,
            "description": inv.lines.data[0].description if inv.lines.data else (inv.description or "Subscription payment"),
            "amount": inv.amount_paid / 100,
            "currency": (inv.currency or "usd").upper(),
            "status": inv.status,
            "invoice_pdf": inv.invoice_pdf,
            "hosted_invoice_url": inv.hosted_invoice_url,
            "type": "credit" if inv.amount_paid < 0 else "debit",
        })
    return result


def create_addfunds_checkout_session(user_id: str, email: str, amount: float, customer_id: str = None):
    """
    Create a Stripe checkout session for a one-time wallet top-up.
    """
    session_params = {
        "payment_method_types": ["card"],
        "line_items": [{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "RAAMP Wallet Top-Up"},
                "unit_amount": int(round(amount * 100)),
            },
            "quantity": 1,
        }],
        "mode": "payment",
        "success_url": f"{Config.FRONTEND_URL}/dashboard/billing?funds_added=true&amount={amount}",
        "cancel_url": f"{Config.FRONTEND_URL}/dashboard/billing?canceled=true",
        "metadata": {
            "userId": user_id,
            "type": "wallet_topup",
            "amount": str(amount),
        },
    }
    
    if customer_id:
        session_params["customer"] = customer_id
    else:
        session_params["customer_email"] = email

    return stripe.checkout.Session.create(**session_params)
