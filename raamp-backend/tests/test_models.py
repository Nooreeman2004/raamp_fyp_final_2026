"""
Quick diagnostic: checks which models are accessible with the current API key.
Run: python test_models.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
text_model = os.getenv("GEMINI_TEXT_MODEL", "gemini-3-flash-preview")
image_model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview")

client = genai.Client(api_key=api_key)
print(f"\n{'='*50}")
print(f"API Key (first 10): {api_key[:10]}...")
print(f"Text model: {text_model}")
print(f"Image model: {image_model}")
print(f"{'='*50}\n")

# --- Test 1: Text model via native SDK ---
print(f"[TEST 1] Native SDK text: {text_model}")
try:
    response = client.models.generate_content(
        model=text_model,
        contents='Return this JSON exactly: {"status": "ok"}',
        config=types.GenerateContentConfig(max_output_tokens=50, temperature=0.1)
    )
    print(f"  ✅ SUCCESS: {response.text[:100]}")
except Exception as e:
    print(f"  ❌ FAILED: {type(e).__name__}: {e}")

# --- Test 2: OpenAI-compatible API ---
print(f"\n[TEST 2] OpenAI-compat API: {text_model}")
try:
    from openai import OpenAI
    openai_client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    response = openai_client.chat.completions.create(
        model=text_model,
        messages=[{"role": "user", "content": 'Return: {"status": "ok"}'}],
        max_tokens=50,
        response_format={"type": "json_object"}
    )
    print(f"  ✅ SUCCESS: {response.choices[0].message.content}")
except Exception as e:
    print(f"  ❌ FAILED: {type(e).__name__}: {e}")

# --- Test 3: Fallback model gemini-1.5-flash via OpenAI-compat ---
print(f"\n[TEST 3] OpenAI-compat fallback: gemini-1.5-flash")
try:
    from openai import OpenAI
    openai_client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    response = openai_client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=[{"role": "user", "content": 'Return: {"status": "ok"}'}],
        max_tokens=50,
        response_format={"type": "json_object"}
    )
    print(f"  ✅ SUCCESS: {response.choices[0].message.content}")
except Exception as e:
    print(f"  ❌ FAILED: {type(e).__name__}: {e}")

# --- Test 4: gemini-2.0-flash via OpenAI-compat ---
print(f"\n[TEST 4] OpenAI-compat: gemini-2.0-flash")
try:
    openai_client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    response = openai_client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[{"role": "user", "content": 'Return: {"status": "ok"}'}],
        max_tokens=50,
        response_format={"type": "json_object"}
    )
    print(f"  ✅ SUCCESS: {response.choices[0].message.content}")
except Exception as e:
    print(f"  ❌ FAILED: {type(e).__name__}: {e}")

# --- Test 5: Image model ---
print(f"\n[TEST 5] Image generation: {image_model}")
try:
    response = client.models.generate_image(
        model=image_model,
        prompt="A simple red circle on white background",
        config=types.GenerateImageConfig(number_of_images=1, aspect_ratio="1:1")
    )
    if response.generated_images:
        print(f"  ✅ SUCCESS: Got {len(response.generated_images)} image(s)")
    else:
        print(f"  ❌ No images returned")
except Exception as e:
    print(f"  ❌ FAILED (generate_image): {type(e).__name__}: {e}")
    # Try generate_content for image
    print(f"  Trying generate_content with IMAGE modality...")
    try:
        resp2 = client.models.generate_content(
            model=image_model,
            contents="A simple red circle on white background",
            config=types.GenerateContentConfig(response_modalities=["TEXT","IMAGE"])
        )
        has_img = any(p.inline_data for p in resp2.candidates[0].content.parts if hasattr(p, 'inline_data') and p.inline_data)
        print(f"  {'✅ Got image data' if has_img else '❌ No inline_data found'}")
    except Exception as e2:
        print(f"  ❌ FAILED (generate_content): {type(e2).__name__}: {e2}")

print(f"\n{'='*50}")
print("Diagnostic complete.")
print(f"{'='*50}\n")
