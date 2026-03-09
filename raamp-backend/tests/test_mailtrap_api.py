import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_token = os.getenv("MAILTRAP_API_TOKEN", "78049356a1e16f8ffe78c57832a34eed")
inbox_id = "4206318" # From user's request
url = f"https://sandbox.api.mailtrap.io/api/send/{inbox_id}"

payload = {
    "from": {
        "email": "hello@raamp.ai",
        "name": "RAAMP Assistant"
    },
    "to": [
        {
            "email": "malik.noor.eman@gmail.com"
        }
    ],
    "subject": "You are awesome!",
    "text": "Congrats for sending test email with Mailtrap from RAAMP Assistant!",
    "category": "Integration Test"
}

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

print(f"Sending email via Mailtrap API to {payload['to'][0]['email']}...")
response = requests.post(url, headers=headers, data=json.dumps(payload))

if response.status_code == 200:
    print("✅ Success!")
    print(response.json())
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)
