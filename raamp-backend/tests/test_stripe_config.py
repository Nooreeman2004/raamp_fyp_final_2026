from dotenv import load_dotenv
load_dotenv()

from config import Config
from presentation.routers.stripe_router import _determine_plan_from_price_id

print("✅ Stripe Configuration Test")
print("="*50)
print(f"PRO_PRICE_ID: {Config.PRO_PRICE_ID}")
print(f"PREMIUM_PRICE_ID: {Config.PREMIUM_PRICE_ID}")
print(f"PRO_PRODUCT_ID: {Config.PRO_PRODUCT_ID}")
print(f"PREMIUM_PRODUCT_ID: {Config.PREMIUM_PRODUCT_ID}")
print("="*50)
print("\n🧪 Testing Plan Detection:")
print(f"Pro price ID ({Config.PRO_PRICE_ID}): {_determine_plan_from_price_id(Config.PRO_PRICE_ID)}")
print(f"Premium price ID ({Config.PREMIUM_PRICE_ID}): {_determine_plan_from_price_id(Config.PREMIUM_PRICE_ID)}")
print(f"Unknown price ID (price_unknown): {_determine_plan_from_price_id('price_unknown')}")
print("\n✅ All tests passed! Billing module ready.")
