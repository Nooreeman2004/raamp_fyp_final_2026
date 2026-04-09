__test__ = False  # pytest: this is a manual smoke script (imports full app)

from fastapi.testclient import TestClient
from main import app
from presentation.routers.auth_router import get_current_user_email
import asyncio

# Override the auth dependency to always return a test email
def override_get_current_user_email():
    return "test@example.com"

app.dependency_overrides[get_current_user_email] = override_get_current_user_email

client = TestClient(app)

print("Checking /library ...")
response = client.get("/api/assets/library")
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(response.json())

print("Checking /captions ...")
response = client.get("/api/assets/captions")
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(response.json())
