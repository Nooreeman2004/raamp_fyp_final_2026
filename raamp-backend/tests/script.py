# test_openai_quota.py
import os
from openai import OpenAI

# Test the key
client = OpenAI(api_key="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")

try:
    # Test with a simple completion
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'API key works!'"}],
        max_tokens=10
    )
    print("✅ API Key is valid!")
    print(f"Response: {response.choices[0].message.content}")
    print("\nTo check quota details, visit:")
    print("https://platform.openai.com/usage")
except Exception as e:
    print(f"❌ Error: {e}")
