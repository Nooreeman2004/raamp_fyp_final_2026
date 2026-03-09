#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Video Generation Test
============================
Quick test script to verify standard video generation is working.

This script:
1. Generates a video prompt using Gemini
2. Generates a single test video using Veo 3.1
3. Saves the result to generated_videos/

Usage:
    python tests/quick_video_test.py
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

from application.services.video_generation_service import VideoGenerationService

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("="*70)
print("  🎥 QUICK VIDEO GENERATION TEST")
print("="*70)

# Check API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY not found!")
    sys.exit(1)

print(f"✅ API Key: {api_key[:15]}...")

try:
    # Initialize service
    print("\n⏳ Initializing Video Generation Service...")
    video_service = VideoGenerationService()
    print(f"✅ Service initialized")
    print(f"   Text Model: {video_service.text_model}")
    print(f"   Video Model: {video_service.video_model}")
    
    # Test prompt
    test_input = "A cinematic product showcase of a luxury watch on a rotating platform with dramatic lighting"
    
    # Test brand context
    brand_context = {
        "business_name": "TimeCraft",
        "business_type": "Luxury Watches",
        "tone_of_voice": "Elegant and sophisticated",
        "primary_color": "Gold and Black"
    }
    
    # Choose aspect ratio
    print("\n📐 Aspect Ratio Options:")
    print("   1. 16:9 (Horizontal - YouTube, Facebook)")
    print("   2. 1:1 (Square - Instagram Feed)")
    aspect_choice = input("   Enter 1 or 2 (default: 1): ").strip() or "1"
    aspect_ratio = "16:9" if aspect_choice == "1" else "1:1"
    
    print(f"\n💡 Test Input: {test_input}")
    print(f"🏢 Brand: {brand_context['business_name']}")
    print(f"📐 Aspect Ratio: {aspect_ratio}")
    
    # Step 1: Generate video prompt
    print("\n⏳ Step 1: Generating video prompt with Gemini...")
    video_prompt = video_service.generate_video_prompt(
        test_input, 
        brand_context, 
        aspect_ratio
    )
    
    print("\n✅ Video Prompt Generated:")
    print("─"*70)
    print(video_prompt)
    print("─"*70)
    
    # Step 2: Generate one test video
    proceed = input("\n🎬 Generate a test video? (y/n): ").strip().lower()
    
    if proceed == 'y':
        print("\n⏳ Step 2: Generating video (this may take 2-3 minutes)...")
        print("⏰ Please wait while Veo 3.1 generates your video...")
        
        # Create output folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_folder = Path(f"generated_videos/test_{timestamp}")
        output_folder.mkdir(parents=True, exist_ok=True)
        
        filename = str(output_folder / "test_video.mp4")
        
        # Generate single video
        result = video_service.generate_single_video(
            video_prompt=video_prompt,
            filename=filename,
            aspect_ratio=aspect_ratio,
            duration_seconds=8
        )
        
        if result:
            print(f"\n✅ SUCCESS! Video saved to: {result}")
            print("─"*70)
            print("💡 Tips:")
            print(f"   • Video aspect ratio: {aspect_ratio}")
            print("   • Duration: 8 seconds")
            print("   • Perfect for social media posts!")
            print("─"*70)
        else:
            print("\n❌ Failed to generate video. Check logs for errors.")
    else:
        print("\n❌ Video generation cancelled.")
    
    print("\n✅ Test completed!")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*70)
