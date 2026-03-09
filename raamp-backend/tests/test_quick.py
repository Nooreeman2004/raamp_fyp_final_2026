#!/usr/bin/env python3
"""
Quick Test Script - One-command testing for OpenAI RAG Chatbot
==============================================================
Run this script for instant verification that the chatbot is working.

Usage:
    python test_quick.py              # Run sanity check
    python test_quick.py --full       # Run all integration tests
    python test_quick.py --api        # Test API endpoints
    python test_quick.py --help       # Show help
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def quick_sanity_check():
    """Run a quick sanity check (30 seconds)"""
    print("\n" + "=" * 70)
    print("QUICK SANITY CHECK (30 seconds)")
    print("=" * 70 + "\n")
    
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check API key
        print("1. Checking environment...")
        if not os.getenv("OPENAI_API_KEY"):
            print("   ❌ OPENAI_API_KEY not found")
            print("   Please add it to your .env file")
            return False
        print("   ✅ OPENAI_API_KEY is set")
        
        # Test imports
        print("\n2. Testing imports...")
        from application.services.rag.raamp_generation import RAAMPGenerator
        print("   ✅ Imports successful")
        
        # Test initialization
        print("\n3. Initializing generator...")
        generator = RAAMPGenerator()
        print(f"   ✅ Generator initialized (model: {generator.model_name})")
        
        # Test simple query
        print("\n4. Testing simple query...")
        response = generator.generate_response("Hello")
        assert response and response.answer
        print(f"   ✅ Response received ({len(response.answer)} chars)")
        print(f"   Preview: {response.answer[:100]}...")
        
        # Test RAG
        print("\n5. Testing RAG retrieval...")
        response = generator.generate_response("What is RAAMP?")
        assert response and response.sources
        print(f"   ✅ Retrieval successful ({len(response.sources)} sources)")
        
        # Test conversation
        print("\n6. Testing conversation...")
        from application.services.rag.raamp_generation import RAMPAssistant
        assistant = RAMPAssistant(session_id="quick-test")
        result = assistant.ask("Hello")
        assert result and result.get('answer')
        print(f"   ✅ Conversation mode working")
        
        print("\n" + "=" * 70)
        print("✅ SANITY CHECK PASSED - Chatbot is working!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ SANITY CHECK FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_integration_tests():
    """Run full integration test suite"""
    print("\n" + "=" * 70)
    print("RUNNING FULL INTEGRATION TESTS")
    print("=" * 70 + "\n")
    
    import subprocess
    
    test_file = Path(__file__).parent / "test_chatbot_rag_integration.py"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def run_api_tests():
    """Run API endpoint tests"""
    print("\n" + "=" * 70)
    print("RUNNING API TESTS")
    print("=" * 70 + "\n")
    
    print("⚠️  Make sure the API is running: uvicorn main:app --reload\n")
    
    import subprocess
    
    test_file = Path(__file__).parent / "test_chatbot_api_endpoints.py"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def run_simple_test():
    """Run simple test script"""
    print("\n" + "=" * 70)
    print("RUNNING SIMPLE API TEST")
    print("=" * 70 + "\n")
    
    import subprocess
    
    test_file = Path(__file__).parent / "test_chatbot_simple.py"
    
    cmd = [sys.executable, str(test_file)]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Quick test script for OpenAI RAG Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_quick.py              # Quick sanity check (30s)
  python test_quick.py --full       # Full integration tests
  python test_quick.py --api        # API endpoint tests
  python test_quick.py --simple     # Simple API test script
  python test_quick.py --all        # Run everything
        """
    )
    
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full integration test suite with pytest'
    )
    
    parser.add_argument(
        '--api',
        action='store_true',
        help='Run API endpoint tests (requires backend running)'
    )
    
    parser.add_argument(
        '--simple',
        action='store_true',
        help='Run simple API test script'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all tests'
    )
    
    args = parser.parse_args()
    
    # Default to sanity check if no args
    if not (args.full or args.api or args.simple or args.all):
        success = quick_sanity_check()
        return 0 if success else 1
    
    results = []
    
    # Run requested tests
    if args.all:
        print("\n🚀 Running ALL tests...")
        results.append(("Sanity Check", quick_sanity_check()))
        results.append(("Integration Tests", run_integration_tests()))
        results.append(("API Tests", run_api_tests()))
    else:
        if args.full:
            results.append(("Integration Tests", run_integration_tests()))
        
        if args.api:
            results.append(("API Tests", run_api_tests()))
        
        if args.simple:
            results.append(("Simple Test", run_simple_test()))
    
    # Print summary
    if len(results) > 1:
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        for name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{status}: {name}")
        
        all_passed = all(passed for _, passed in results)
        
        if all_passed:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n⚠️  Some tests failed")
            return 1
    
    # Single test result
    return 0 if results[0][1] else 1


if __name__ == "__main__":
    sys.exit(main())
