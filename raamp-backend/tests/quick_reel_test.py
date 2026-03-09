#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Reel Generation Test
===========================
Quick test script to verify Instagram Reel generation is working.

This script:
1. Generates a Reel prompt using Gemini
2. Generates a single test Reel using Veo 3.1
3. Saves the result to generated_reels/

Usage:
    python tests/quick_reel_test.py
"""

import os
import sys
import io
from pathlib import Path
from datetime import datetime

# Ensure UTF-8 encoding on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from application.services.reel_generation_service import ReelGenerationService

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("="*70)
print("  🎬 QUICK REEL GENERATION TEST")
print("="*70)

# Check API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found!")
    sys.exit(1)

print(f"✅ API Key: {api_key[:15]}...")

try:
    # Initialize service
    print("\n⏳ Initializing Reel Generation Service...")
    reel_service = ReelGenerationService()
    print(f"✅ Service initialized")
    print(f"   Text Model: {reel_service.text_model}")
    print(f"   Video Model: {reel_service.video_model}")
    
    # Test prompt
    test_input = "Create a Reel showing a coffee shop's signature latte with beautiful latte art"
    
    # Test brand context
    brand_context = {
        "business_name": "Brew & Co.",
        "business_type": "Coffee Shop",
        "tone_of_voice": "Cozy and inviting",
        "primary_color": "Warm brown"
    }
    
    print(f"\n💡 Test Input: {test_input}")
    print(f"🏢 Brand: {brand_context['business_name']}")
    
    # Step 1: Generate Reel prompt
    print("\n⏳ Step 1: Generating Reel prompt with Gemini...")
    reel_prompt = reel_service.generate_reel_prompt(test_input, brand_context)
    
    print("\n✅ Reel Prompt Generated:")
    print("─"*70)
    print(reel_prompt)
    print("─"*70)
    
    # Step 2: Generate one test Reel
    proceed = input("\n🎬 Generate a test Reel? (y/n): ").strip().lower()
    
    if proceed == 'y':
        print("\n⏳ Step 2: Generating Reel video (this may take 2-3 minutes)...")
        print("⏰ Please wait while Veo 3.1 generates your Reel...")
        
        # Create output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_folder = Path(f"generated_reels/test_{timestamp}")
        output_folder.mkdir(parents=True, exist_ok=True)
        
        filename = str(output_folder / "test_reel.mp4")
        
        # Generate single Reel
        result = reel_service.generate_single_reel(
            reel_prompt=reel_prompt,
            filename=filename,
            duration_seconds=12
        )
        
        if result:
            print(f"\n✅ SUCCESS! Reel saved to: {result}")
            print("─"*70)
            print("💡 Tips:")
            print("   • Video is 9:16 aspect ratio (vertical)")
            print("   • Duration: 12 seconds")
            print("   • Perfect for Instagram Reels!")
            print("─"*70)
        else:
            print("\n❌ Failed to generate Reel. Check logs for errors.")
    else:
        print("\n❌ Reel generation cancelled.")
    
    print("\n✅ Test completed!")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*70)
