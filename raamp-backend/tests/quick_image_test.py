#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test to see image generation error"""
import os
import sys
import io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from google import genai

api_key = os.getenv("GEMINI_API_KEY")
image_model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview")

print(f"Testing image generation with: {image_model}")
print(f"API Key: {api_key[:15]}...")
print()

try:
    client = genai.Client(api_key=api_key)
    print(f"Generating image...")
    
    response = client.models.generate_content(
        model=image_model,
        contents="A delicious scoop of strawberry ice cream in a waffle cone"
    )
    
    print("[SUCCESS] Image generation successful!")
    print(f"Response type: {type(response)}")
    print(f"Has parts: {hasattr(response, 'parts')}")
    
    if hasattr(response, 'text'):
        print(f"Text: {response.text[:100]}")
    
    if hasattr(response, 'parts'):
        print(f"Number of parts: {len(response.parts)}")
        for i, part in enumerate(response.parts):
            print(f"  Part {i}: {type(part)}")
            if hasattr(part, 'inline_data'):
                print(f"    Has inline_data with mime_type: {part.inline_data.mime_type}")
                print(f"    Data length: {len(part.inline_data.data)} bytes")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
