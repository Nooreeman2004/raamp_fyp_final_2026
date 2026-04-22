import urllib.request
import urllib.error
import json
import jwt
from datetime import datetime, timedelta
import os

secret = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
# The DB has a seed user "admin@example.com" or just something that exists
payload = {
    "email": "test@example.com",
    "exp": datetime.utcnow() + timedelta(minutes=15)
}
token = jwt.encode(payload, secret, algorithm="HS256")

url = "http://localhost:8000/api/auth/profile"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

try:
    print("Sending request with valid token...")
    response = urllib.request.urlopen(req, timeout=15)
    data = response.read()
    print("SUCCESS STATUS:", response.status)
    print("RESPONSE:", data.decode())
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code)
    print("REASON:", e.read())
except Exception as e:
    print("OTHER ERROR:", repr(e))
