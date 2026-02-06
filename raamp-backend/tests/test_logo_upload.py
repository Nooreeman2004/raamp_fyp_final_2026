"""
Quick test to verify logo upload works with local storage
"""
import requests
import os

# Create a simple test image (1x1 PNG)
# PNG header for a 1x1 transparent image
test_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

print("Testing logo upload to local storage...")

# You need a valid JWT token - get one from your browser's localStorage
# For now, let's just test the endpoint is available
response = requests.get("http://localhost:8000/health")
print(f"Backend health check: {response.status_code}")
print(f"Response: {response.json()}")

# To test upload, you would need:
# headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
# files = {"logo": ("test.png", test_png, "image/png")}
# response = requests.post("http://localhost:8000/api/brand-alignment/upload-logo", 
#                         headers=headers, files=files)
# print(f"Upload response: {response.status_code}")
# print(f"Response: {response.json()}")
