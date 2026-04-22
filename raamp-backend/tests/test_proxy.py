import urllib.request
import urllib.error
import jwt
from datetime import datetime, timedelta
import os

secret = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
# Real user payload
payload = {
    "email": "test@example.com",
    "exp": datetime.utcnow() + timedelta(minutes=15)
}
token = jwt.encode(payload, secret, algorithm="HS256")

# Targeting vite dev proxy on port 8080
url = "http://localhost:8080/api/auth/profile"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

try:
    print("Sending request through proxy...")
    response = urllib.request.urlopen(req, timeout=15)
    print("SUCCESS STATUS:", response.status)
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code)
    print("REASON:", e.read().decode())
except Exception as e:
    print("OTHER ERROR:", repr(e))
