"""Quick test of the new endpoints"""
import requests

print("Testing new endpoints...")
print("=" * 80)

# Test 1: Simple endpoint (no auth)
try:
    r = requests.get("http://localhost:8000/api/comments/test-moderation-simple")
    print(f"✅ Test endpoint: {r.status_code}")
    print(f"   Response: {r.json()}")
except Exception as e:
    print(f"❌ Test endpoint failed: {e}")

print()

# Test 2: Real moderation endpoint (requires auth)
try:
    r = requests.get("http://localhost:8000/api/comments/moderation?limit=100")
    print(f"✅ Moderation endpoint: {r.status_code}")
    print(f"   Response: {r.json()}")
except Exception as e:
    print(f"❌ Moderation endpoint failed: {e}")
