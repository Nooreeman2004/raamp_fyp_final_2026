#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Content Generator Demo
======================
Interactive menu-driven demo for testing Image, Video, and Reel generation.

This script demonstrates the full content generation pipeline:
1. Image Generation - Using Gemini (Nano Banana style)
2. Video Generation - Using Veo 3.1 (horizontal/square videos)
3. Instagram Reel Generation - Using Veo 3.1 (vertical 9:16, 8-15s)

Usage:
    python content_generator_demo.py
"""

import os
import sys
import io
import asyncio
from pathlib import Path
from datetime import datetime

# Ensure UTF-8 encoding on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# Import our services
from application.services.image_generation_service import ImageGenerationService
from application.services.video_generation_service import VideoGenerationService
from application.services.reel_generation_service import ReelGenerationService

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print the application banner."""
    print("\n" + "="*70)
    print("  🎨 AI CONTENT GENERATOR - Image | Video | Reel")
    print("="*70)
    print("  Powered by Google Gemini & Veo 3.1")
    print("="*70 + "\n")


def print_menu():
    """Print the main menu."""
    print("\n📋 What do you want to generate?")
    print("   1️⃣  Image (Social Media Post)")
    print("   2️⃣  Video (16:9 or 1:1)")
    print("   3️⃣  Instagram Reel (9:16, 8-15s)")
    print("   4️⃣  Exit")
    print()


def get_user_input(prompt: str) -> str:
    """Get user input with validation."""
    while True:
        user_input = input(prompt).strip()
        if user_input:
            return user_input
        print("❌ Input cannot be empty. Please try again.\n")


def get_brand_context() -> dict:
    """Get optional brand context from user."""
    print("\n🏢 Brand Context (Optional - press Enter to skip each):")
    
    brand_context = {}
    
    business_name = input("   Business name: ").strip()
    if business_name:
        brand_context["business_name"] = business_name
    
    business_type = input("   Industry/Type: ").strip()
    if business_type:
        brand_context["business_type"] = business_type
    
    tone = input("   Tone (e.g., professional, playful): ").strip()
    if tone:
        brand_context["tone_of_voice"] = tone
    
    primary_color = input("   Primary Color: ").strip()
    if primary_color:
        brand_context["primary_color"] = primary_color
    
    return brand_context if brand_context else None


async def handle_image_generation(image_service: ImageGenerationService):
    """Handle image generation flow."""
    print("\n" + "─"*70)
    print("🎨 IMAGE GENERATION MODE")
    print("─"*70)
    
    # Get user input
    campaign_idea = get_user_input("\n💡 Describe your image idea: ")
    
    # Optional: Get brand context
    use_brand = input("\n🏢 Include brand context? (y/n): ").strip().lower()
    brand_context = get_brand_context() if use_brand == 'y' else {}
    
    try:
        # Step 1: Generate image prompt
        print("\n⏳ Generating image prompt...")
        image_prompt = image_service.generate_image_prompt(campaign_idea, brand_context or {})
        
        print("\n✅ Generated Image Prompt:")
        print("─"*70)
        print(image_prompt)
        print("─"*70)
        
        # Step 2: Generate images
        proceed = input("\n📸 Generate 3 image variations? (y/n): ").strip().lower()
        if proceed != 'y':
            print("❌ Image generation cancelled.")
            return
        
        print("\n⏳ Generating 3 image variations (this may take 30-60 seconds)...")
        
        # Generate unique campaign ID
        campaign_id = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate images
        image_urls = await image_service.generate_images(
            image_prompt=image_prompt,
            campaign_id=campaign_id,
            count=3
        )
        
        if image_urls:
            print(f"\n✅ Success! {len(image_urls)} images generated:")
            print("─"*70)
            for i, url in enumerate(image_urls, 1):
                # Convert URL back to file path for display
                file_path = url.replace("/api/generated/", "generated_images/")
                print(f"   {i}. {file_path}")
            print("─"*70)
        else:
            print("\n❌ No images were generated. Check logs for errors.")
    
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        print(f"\n❌ Error: {e}")


async def handle_video_generation(video_service: VideoGenerationService):
    """Handle video generation flow."""
    print("\n" + "─"*70)
    print("🎥 VIDEO GENERATION MODE")
    print("─"*70)
    
    # Get user input
    video_idea = get_user_input("\n💡 Describe your video idea: ")
    
    # Choose aspect ratio
    print("\n📐 Choose aspect ratio:")
    print("   1. 16:9 (Horizontal - YouTube, Facebook)")
    print("   2. 1:1 (Square - Instagram Feed)")
    aspect_choice = input("   Enter 1 or 2: ").strip()
    aspect_ratio = "16:9" if aspect_choice == "1" else "1:1"
    
    # Optional: Get brand context
    use_brand = input("\n🏢 Include brand context? (y/n): ").strip().lower()
    brand_context = get_brand_context() if use_brand == 'y' else {}
    
    try:
        # Step 1: Generate video prompt
        print("\n⏳ Generating video prompt...")
        video_prompt = video_service.generate_video_prompt(
            video_idea, 
            brand_context, 
            aspect_ratio
        )
        
        print("\n✅ Generated Video Prompt:")
        print("─"*70)
        print(video_prompt)
        print("─"*70)
        
        # Step 2: Generate videos
        proceed = input("\n🎬 Generate 3 video variations? (y/n): ").strip().lower()
        if proceed != 'y':
            print("❌ Video generation cancelled.")
            return
        
        print("\n⏳ Generating 3 video variations (this may take 3-5 minutes)...")
        print("⏰ Videos are being generated in parallel. Please wait...")
        
        # Generate unique folder
        output_folder = f"generated_videos/vid_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate videos (sync version for simplicity in demo)
        video_paths = video_service.generate_videos_sync(
            video_prompt=video_prompt,
            output_folder=output_folder,
            count=3,
            aspect_ratio=aspect_ratio,
            duration_seconds=8
        )
        
        if video_paths:
            print(f"\n✅ Success! {len(video_paths)} videos generated:")
            print("─"*70)
            for i, path in enumerate(video_paths, 1):
                print(f"   {i}. {path}")
            print("─"*70)
        else:
            print("\n❌ No videos were generated. Check logs for errors.")
    
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        print(f"\n❌ Error: {e}")


async def handle_reel_generation(reel_service: ReelGenerationService):
    """Handle Instagram Reel generation flow."""
    print("\n" + "─"*70)
    print("📱 INSTAGRAM REEL GENERATION MODE")
    print("─"*70)
    
    # Get user input
    reel_idea = get_user_input("\n💡 Describe your Reel idea: ")
    
    # Optional: Get brand context
    use_brand = input("\n🏢 Include brand context? (y/n): ").strip().lower()
    brand_context = get_brand_context() if use_brand == 'y' else {}
    
    try:
        # Step 1: Generate Reel prompt
        print("\n⏳ Generating Reel script/prompt...")
        reel_prompt = reel_service.generate_reel_prompt(reel_idea, brand_context)
        
        print("\n✅ Generated Reel Prompt:")
        print("─"*70)
        print(reel_prompt)
        print("─"*70)
        
        # Step 2: Generate Reels
        proceed = input("\n🎬 Generate 3 Reel variations (8-15s each)? (y/n): ").strip().lower()
        if proceed != 'y':
            print("❌ Reel generation cancelled.")
            return
        
        print("\n⏳ Generating 3 Reel variations (this may take 3-5 minutes)...")
        print("⏰ Reels are being generated in parallel. Please wait...")
        
        # Generate unique folder
        output_folder = f"generated_reels/reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate Reels (sync version for simplicity in demo)
        reel_paths = reel_service.generate_reels_sync(
            reel_prompt=reel_prompt,
            output_folder=output_folder,
            count=3,
            duration_seconds=12
        )
        
        if reel_paths:
            print(f"\n✅ Success! {len(reel_paths)} Reels generated:")
            print("─"*70)
            for i, path in enumerate(reel_paths, 1):
                print(f"   {i}. {path}")
            print("─"*70)
            print("\n💡 Tip: Upload these to Instagram as Reels for maximum engagement!")
        else:
            print("\n❌ No Reels were generated. Check logs for errors.")
    
    except Exception as e:
        logger.error(f"Reel generation error: {e}")
        print(f"\n❌ Error: {e}")


async def main():
    """Main application loop."""
    print_banner()
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not found in environment variables!")
        print("   Please set your API key in .env file")
        return
    
    print(f"✅ API Key loaded: {api_key[:15]}...")
    
    # Initialize services
    try:
        print("⏳ Initializing services...")
        image_service = ImageGenerationService()
        video_service = VideoGenerationService()
        reel_service = ReelGenerationService()
        print("✅ All services initialized successfully!\n")
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        return
    
    # Main menu loop
    while True:
        print_menu()
        choice = input("👉 Enter your choice (1-4): ").strip()
        
        if choice == "1":
            # Image generation
            await handle_image_generation(image_service)
        
        elif choice == "2":
            # Video generation
            await handle_video_generation(video_service)
        
        elif choice == "3":
            # Reel generation
            await handle_reel_generation(reel_service)
        
        elif choice == "4":
            # Exit
            print("\n👋 Thanks for using AI Content Generator!")
            print("="*70 + "\n")
            break
        
        else:
            print("\n❌ Invalid choice. Please enter 1, 2, 3, or 4.\n")
        
        # Ask if user wants to continue
        if choice in ["1", "2", "3"]:
            continue_choice = input("\n🔄 Generate more content? (y/n): ").strip().lower()
            if continue_choice != 'y':
                print("\n👋 Thanks for using AI Content Generator!")
                print("="*70 + "\n")
                break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
