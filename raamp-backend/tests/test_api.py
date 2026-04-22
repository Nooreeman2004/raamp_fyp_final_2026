import urllib.request
import urllib.error
import json
import jwt
from datetime import datetime, timedelta
import os

# Generate a valid short-lived token using the project's secret key
secret = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
payload = {
    "sub": "test@example.com",
    "exp": datetime.utcnow() + timedelta(minutes=15)
}
token = jwt.encode(payload, secret, algorithm="HS256")

# Make HTTP Request
url = "http://localhost:8000/api/assets/library?page=1&per_page=50"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

try:
    response = urllib.request.urlopen(req)
    data = response.read()
    print("SUCCESS STATUS:", response.status)
    print("RESPONSE (truncated):", data[:200])
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code)
    print("REASON:", e.read())
except Exception as e:
    print("OTHER ERROR:", repr(e))
