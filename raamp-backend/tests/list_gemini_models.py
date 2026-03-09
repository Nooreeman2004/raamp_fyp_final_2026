"""
List Available Gemini Models
=============================
"""

import os
from dotenv import load_dotenv
load_dotenv()

from google import genai

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key: {api_key[:15]}..." if api_key else "NOT SET")

client = genai.Client(api_key=api_key)

print("\nAvailable Gemini Models:")
print("=" * 80)

try:
    models = client.models.list()
    for model in models:
        print(f"\n📦 {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description[:100]}..." if len(model.description) > 100 else f"   Description: {model.description}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"   Supported Methods: {model.supported_generation_methods}")
except Exception as e:
    print(f"Error listing models: {e}")
