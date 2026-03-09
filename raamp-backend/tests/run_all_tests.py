"""
Test Runner for OpenAI RAG Chatbot
==================================
Runs all test suites with comprehensive reporting.
"""

import subprocess
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


def print_header(title: str, char: str = "="):
    """Print a formatted header"""
    border = char * 70
    print(f"\n{border}")
    print(title.center(70))
    print(f"{border}\n")


def check_prerequisites():
    """Check that all prerequisites are met"""
    print_header("Checking Prerequisites", "-")
    
    issues = []
    
    # Check OpenAI API Key
    if not os.getenv("OPENAI_API_KEY"):
        issues.append("❌ OPENAI_API_KEY not found in environment variables")
        issues.append("   Please add it to your .env file")
    else:
        print("✅ OPENAI_API_KEY is set")
    
    # Check if pytest is installed
    try:
        import pytest
        print(f"✅ pytest is installed (version {pytest.__version__})")
    except ImportError:
        issues.append("❌ pytest is not installed")
        issues.append("   Install with: pip install pytest pytest-asyncio")
    
    # Check if langchain_openai is installed
    try:
        import langchain_openai
        print("✅ langchain_openai is installed")
    except ImportError:
        issues.append("❌ langchain_openai is not installed")
        issues.append("   Install with: pip install langchain-openai")
    
    # Check if openai is installed
    try:
        import openai
        print(f"✅ openai is installed (version {openai.__version__})")
    except ImportError:
        issues.append("❌ openai is not installed")
        issues.append("   Install with: pip install openai")
    
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(issue)
        return False
    
    print("\n✅ All prerequisites met!")
    return True


def run_integration_tests():
    """Run integration tests (RAG functionality)"""
    print_header("Running Integration Tests (RAG Chatbot)")
    
    test_file = Path(__file__).parent / "test_chatbot_rag_integration.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def run_api_tests():
    """Run API endpoint tests"""
    print_header("Running API Endpoint Tests")
    
    print("⚠️  Note: API tests require the backend to be running:")
    print("   uvicorn main:app --reload\n")
    
    response = input("Is the API running? (y/n): ").strip().lower()
    
    if response != 'y':
        print("⏭️  Skipping API tests")
        return True
    
    test_file = Path(__file__).parent / "test_chatbot_api_endpoints.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v",
        "--tb=short",
        "--color=yes"
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def run_quick_sanity_check():
    """Run a quick sanity check"""
    print_header("Running Quick Sanity Check", "-")
    
    try:
        print("1. Testing imports...")
        from application.services.rag.raamp_generation import RAAMPGenerator, RAMPAssistant
        print("   ✅ Imports successful")
        
        print("\n2. Testing generator initialization...")
        generator = RAAMPGenerator()
        print(f"   ✅ Generator initialized (model: {generator.model_name})")
        
        print("\n3. Testing simple query...")
        response = generator.generate_response("Hello")
        assert response.answer
        print(f"   ✅ Query successful (response length: {len(response.answer)} chars)")
        
        print("\n4. Testing RAG retrieval...")
        response = generator.generate_response("What is RAAMP?")
        assert response.sources
        print(f"   ✅ Retrieval successful ({len(response.sources)} sources)")
        
        print("\n✅ Sanity check passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Sanity check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_summary_report(results: dict):
    """Generate a summary report"""
    print_header("TEST SUMMARY REPORT")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for passed in results.values() if passed)
    total_count = len(results)
    
    print(f"\n{'-' * 70}")
    print(f"Total: {passed_count}/{total_count} test suites passed")
    print(f"{'-' * 70}")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! OpenAI chatbot is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total_count - passed_count} test suite(s) failed.")
        print("Review the output above for details.")
        return False


def main():
    """Main test runner"""
    print_header("🚀 OPENAI RAG CHATBOT TEST SUITE 🚀")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return 1
    
    # Ask what tests to run
    print_header("Test Selection", "-")
    print("Select tests to run:")
    print("1. Quick sanity check only")
    print("2. Integration tests (RAG functionality)")
    print("3. API endpoint tests")
    print("4. All tests (comprehensive)")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    results = {}
    
    if choice == "1":
        # Quick sanity check
        results["Sanity Check"] = run_quick_sanity_check()
        
    elif choice == "2":
        # Integration tests only
        results["Integration Tests"] = run_integration_tests()
        
    elif choice == "3":
        # API tests only
        results["API Tests"] = run_api_tests()
        
    elif choice == "4":
        # All tests
        results["Sanity Check"] = run_quick_sanity_check()
        
        if results["Sanity Check"]:
            results["Integration Tests"] = run_integration_tests()
            results["API Tests"] = run_api_tests()
        else:
            print("\n⚠️  Sanity check failed. Skipping remaining tests.")
            results["Integration Tests"] = False
            results["API Tests"] = False
    
    else:
        print("❌ Invalid choice")
        return 1
    
    # Generate summary
    all_passed = generate_summary_report(results)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
