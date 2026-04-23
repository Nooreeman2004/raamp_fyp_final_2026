"""Test the HTTP endpoint directly"""
import requests

url = "http://localhost:8000/api/comments/moderation?limit=100"

print("=" * 80)
print("TEST 1: Without Authentication")
print("=" * 80)
try:
    print(f"Testing: {url}")
    response = requests.get(url, headers={"Content-Type": "application/json"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("TEST 2: With Mock JWT Token")
print("=" * 80)
try:
    # Try with a fake token to see if it's an auth issue
    response = requests.get(
        url, 
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer fake_token_for_testing"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
