import urllib.request
import jwt
from datetime import datetime, timedelta
import os

secret = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
payload = {"email": "admin@example.com", "exp": datetime.utcnow() + timedelta(minutes=15)}
token = jwt.encode(payload, secret, algorithm="HS256")

url = "http://localhost:8080/api/assets/library?page=1&per_page=50"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

try:
    print("Testing /api/assets/library via proxy...")
    response = urllib.request.urlopen(req, timeout=15)
    print("SUCCESS STATUS:", response.status)
except Exception as e:
    print("ERROR:", repr(e))
