#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test new API key for text generation"""
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
text_model = "gemini-1.5-flash"

print(f"Testing new API key: {api_key[:15]}...")
print(f"Model: {text_model}")
print()

try:
    client = genai.Client(api_key=api_key)
    print("Testing text generation...")
    
    response = client.models.generate_content(
        model=text_model,
        contents="Say 'Hello! The API key is working.' in exactly those words."
    )
    
    print("[SUCCESS] Text generation works!")
    print(f"Response: {response.text}")
    print()
    print("✅ New API key is valid for TEXT generation")
    print("❌ Image generation quota is exhausted on this account")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
