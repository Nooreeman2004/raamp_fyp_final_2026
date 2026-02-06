"""
QUICKEST TEST - Instagram Post
Just update the credentials and run!
"""
import requests

# ============ UPDATE THESE ============
BASE_URL = "http://localhost:8000"
EMAIL = "mama@gmail.com"              # Using existing user from database
PASSWORD = "Testing123!"              # Try common password (might need to reset)
USERNAME = "mamajee"                   # USERNAME from database
IMAGE_URL = "https://picsum.photos/1080/1080"  # PUBLIC IMAGE URL
CAPTION = """Iftar drive DONATION

A small act of kindness can make someone's Iftar special. Be a part of something meaningful this Ramadan.

DONATE HERE
Title: NOOR E EMAN
Jazzcash: 03355180227

Visit Our Page @kaarefalah

🌙 #Ramadan #Iftar #Charity #Donation #KaarEFalah #RamadanKareem"""
# ======================================

print("🚀 Quick Instagram Post Test\n")

# 0. Try to signup first (in case user doesn't exist)
print("0️⃣  Checking if user exists...")
signup_response = requests.post(f"{BASE_URL}/api/auth/signup", json={
    "username": USERNAME,
    "email": EMAIL,
    "password": PASSWORD,
    "agreed_to_terms": True
})
if signup_response.status_code == 200:
    print("   ⚠️  New user created! Verification email sent.")
    print("   ⚠️  You need to verify email first. Check your email for OTP.")
    print("   For now, continuing to test if account exists...")
elif "already" in signup_response.text.lower():
    print("   ✅ User already exists, proceeding to login...")
else:
    print(f"   ℹ️  Response: {signup_response.text[:100]}...")

# 1. Login
print("\n1️⃣  Logging in...")
r = requests.post(f"{BASE_URL}/api/auth/signin", 
    json={"email": EMAIL, "password": PASSWORD})
if r.status_code != 200:
    print(f"❌ Login failed: {r.text}")
    exit(1)
token = r.json()["access_token"]
print(f"✅ Logged in! Token: {token[:20]}...\n")

# 2. Check connection
print("2️⃣  Checking Instagram connection...")
r = requests.get(f"{BASE_URL}/api/instagram/posting/connection-status",
    headers={"Authorization": f"Bearer {token}"})
data = r.json()
if not data.get("can_post"):
    print(f"❌ Cannot post: {data}")
    exit(1)
print(f"✅ Connected! Page: {data.get('page_name')}\n")

# 3. Post to Instagram
print("3️⃣  Posting to Instagram...")
print(f"   Image: {IMAGE_URL}")
print(f"   Caption: {CAPTION[:50]}...")
print("   ⏳ Please wait 30-60 seconds...\n")

r = requests.post(f"{BASE_URL}/api/instagram/posting/post",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "mode": "post_now",
        "media_url": IMAGE_URL,
        "caption": CAPTION
    },
    timeout=120)

if r.status_code == 200:
    result = r.json()
    print("✅ SUCCESS!")
    print(f"   Status: {result.get('status')}")
    print(f"   IG Post ID: {result.get('instagram_post_id')}")
    print(f"\n🎉 Your post is live on Instagram!")
else:
    print(f"❌ Failed: {r.status_code}")
    print(f"   {r.text}")
