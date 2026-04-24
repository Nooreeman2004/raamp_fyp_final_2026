"""
Check OpenAI API usage and estimate remaining balance
"""
import os
from openai import OpenAI
from datetime import datetime, timedelta

# Initialize client
api_key = os.getenv("OPENAI_API_KEY", "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")
client = OpenAI(api_key=api_key)

print("=" * 60)
print("OpenAI Account Information")
print("=" * 60)

# Test API key validity
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print("✅ API Key Status: VALID")
    print(f"   Key prefix: {api_key[:20]}...")
except Exception as e:
    print(f"❌ API Key Status: INVALID")
    print(f"   Error: {e}")
    exit(1)

print("\n" + "=" * 60)
print("💰 Balance & Usage Information")
print("=" * 60)
print("\nTo check your exact balance and usage:")
print("1. Visit: https://platform.openai.com/usage")
print("2. Login to your OpenAI account")
print("3. View:")
print("   - Current month usage")
print("   - Remaining credits")
print("   - Usage by model")
print("   - Daily breakdown")

print("\n" + "=" * 60)
print("📊 Estimated Costs for RAAMP Features")
print("=" * 60)

costs = {
    "Chatbot (per query)": {
        "Embedding (text-embedding-3-large)": "$0.0001",
        "Response (gpt-4o-mini)": "$0.001-0.003",
        "TTS (optional)": "$0.015",
        "Total per query": "$0.001-0.018"
    },
    "Trend Analysis (per scan)": {
        "Analysis (gpt-4o)": "$0.01-0.03"
    },
    "A/B Image Test (per comparison)": {
        "Vision API (gpt-4o)": "$0.01-0.02"
    }
}

for feature, details in costs.items():
    print(f"\n{feature}:")
    for item, cost in details.items():
        print(f"  • {item}: {cost}")

print("\n" + "=" * 60)
print("💡 Recommendations")
print("=" * 60)
print("For 6-7 test runs:")
print("  • Minimum: $2 (basic testing)")
print("  • Recommended: $5 (comfortable testing)")
print("  • Safe: $10 (plenty for testing + buffer)")

print("\n" + "=" * 60)
print("🔗 Quick Links")
print("=" * 60)
print("Usage Dashboard: https://platform.openai.com/usage")
print("Billing: https://platform.openai.com/account/billing/overview")
print("API Keys: https://platform.openai.com/api-keys")
print("Pricing: https://openai.com/api/pricing/")
print("=" * 60)
