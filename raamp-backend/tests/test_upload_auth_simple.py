"""
Simple Upload Endpoint Authentication Test
Tests that the /api/assets/upload endpoint properly authenticates multipart/form-data requests
"""
import io
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from application.services.jwt_service import JWTService


def test_upload_with_bearer_token():
    """Test file upload with Bearer token in Authorization header"""
    print("\n" + "="*80)
    print("TEST: Upload endpoint with Bearer token authentication")
    print("="*80)
    
    # Generate a valid JWT token
    jwt_service = JWTService()
    test_email = "test@example.com"
    test_token = jwt_service.create_access_token(user_id="testuser123", email=test_email)
    
    print(f"\n1️⃣ Generated JWT token for: {test_email}")
    print(f"   Token (first 50 chars): {test_token[:50]}...")
    
    # Create a test image file
    image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    print(f"\n2️⃣ Created test PNG file")
    print(f"   Size: {len(image_content)} bytes")
    print(f"   Content-Type: image/png")
    
    # Prepare file for upload
    files = {
        'file': ('test_image.png', io.BytesIO(image_content), 'image/png')
    }
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {test_token}"
    }
    
    print(f"\n3️⃣ Sending POST request to http://localhost:8000/api/assets/upload")
    print(f"   Headers:")
    print(f"     - Authorization: Bearer {test_token[:30]}...")
    print(f"\n   NOTE: Make sure backend server is running on localhost:8000!")
    print(f"         Run: python main.py")
    
    try:
        # Make request with Authorization header
        response = requests.post(
            "http://localhost:8000/api/assets/upload",
            files=files,
            headers=headers,
            timeout=10
        )
        
        print(f"\n4️⃣ Response received:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Status: {'✅ SUCCESS' if response.status_code == 200 else '❌ FAILED'}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n   Response Data:")
            print(f"     - asset_id: {data.get('asset_id')}")
            print(f"     - filename: {data.get('filename')}")
            print(f"     - size_bytes: {data.get('size_bytes')}")
            
            # VERIFY FIREBASE_URL IS GONE
            has_firebase = "firebase_url" in data
            print(f"     - firebase_url present: {'❌ YES' if has_firebase else '✅ NO (Correct)'}")
            
            print(f"     - public_url: {data.get('public_url', 'N/A')[:80]}...")
            print(f"     - local_path: {data.get('local_path')}")
            
            # Verify file was saved locally
            local_path = Path(data.get('local_path'))
            if local_path.exists():
                print(f"\n   ✅ File saved locally at: {local_path}")
                print(f"      File size: {local_path.stat().st_size} bytes")
            else:
                print(f"\n   ⚠️ Warning: Local file not found at {local_path}")
            
            print("\n" + "="*80)
            if not has_firebase:
                print("✅ TEST PASSED: Upload successful and schema updated")
            else:
                print("❌ TEST FAILED: firebase_url still present in response")
            print("="*80)
            return not has_firebase
        else:
            print(f"\n   Error Details:")
            try:
                error_data = response.json()
                print(f"     {error_data}")
            except:
                print(f"     {response.text}")
            
            print("\n" + "="*80)
            print("❌ TEST FAILED: Upload returned non-200 status")
            print("="*80)
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to http://localhost:8000")
        print(f"   Make sure the backend server is running:")
        print(f"     cd d:\\raamp-fyp-final\\raamp-backend")
        print(f"     python main.py")
        print("\n" + "="*80)
        print("❌ TEST FAILED: Server not running")
        print("="*80)
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n" + "="*80)
        print(f"❌ TEST FAILED: {e}")
        print("="*80)
        return False


def test_upload_without_token():
    """Test that upload fails without authentication token"""
    print("\n" + "="*80)
    print("TEST: Upload endpoint WITHOUT authentication (should fail)")
    print("="*80)
    
    # Create a test file
    image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
    files = {
        'file': ('test.png', io.BytesIO(image_content), 'image/png')
    }
    
    print(f"\n1️⃣ Sending request WITHOUT Authorization header")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/assets/upload",
            files=files,
            timeout=10
        )
        
        print(f"\n2️⃣ Response received:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Expected: 401 Unauthorized")
        
        if response.status_code == 401:
            print(f"   ✅ Correctly rejected unauthenticated request")
            try:
                error = response.json()
                print(f"   Error message: {error.get('detail')}")
            except:
                pass
            
            print("\n" + "="*80)
            print("✅ TEST PASSED: Unauthenticated request correctly rejected")
            print("="*80)
            return True
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            print("\n" + "="*80)
            print("❌ TEST FAILED: Should have returned 401")
            print("="*80)
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Server not running on localhost:8000")
        return False


def test_upload_with_invalid_token():
    """Test that upload fails with invalid token"""
    print("\n" + "="*80)
    print("TEST: Upload endpoint with INVALID token (should fail)")
    print("="*80)
    
    # Create test file
    image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
    files = {
        'file': ('test.png', io.BytesIO(image_content), 'image/png')
    }
    
    invalid_token = "invalid.token.value"
    
    print(f"\n1️⃣ Sending request with INVALID token: {invalid_token}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/assets/upload",
            files=files,
            headers={
                "Authorization": f"Bearer {invalid_token}"
            },
            timeout=10
        )
        
        print(f"\n2️⃣ Response received:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Expected: 401 Unauthorized")
        
        if response.status_code == 401:
            print(f"   ✅ Correctly rejected invalid token")
            try:
                error = response.json()
                print(f"   Error message: {error.get('detail')}")
            except:
                pass
            
            print("\n" + "="*80)
            print("✅ TEST PASSED: Invalid token correctly rejected")
            print("="*80)
            return True
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            print("\n" + "="*80)
            print("❌ TEST FAILED: Should have returned 401")
            print("="*80)
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Server not running on localhost:8000")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "UPLOAD ENDPOINT AUTHENTICATION TESTS" + " "*22 + "║")
    print("╚" + "═"*78 + "╝")
    
    print("\n🔔 NOTE: These tests require the backend server to be running!")
    print("   Start it with: python main.py")
    print("   Server should be at: http://localhost:8000\n")
    
    results = []
    
    # Run tests
    results.append(("Bearer Token Auth", test_upload_with_bearer_token()))
    results.append(("No Auth (should fail)", test_upload_without_token()))
    results.append(("Invalid Token (should fail)", test_upload_with_invalid_token()))
    
    # Summary
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*30 + "TEST SUMMARY" + " "*36 + "║")
    print("╠" + "═"*78 + "╣")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"║  {status}  │  {test_name:<62}║")
    
    print("╠" + "═"*78 + "╣")
    print(f"║  Total: {passed}/{total} passed" + " "*(61-len(f"Total: {passed}/{total} passed")) + "║")
    print("╚" + "═"*78 + "╝")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Upload endpoint authentication is working correctly.\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED. Please review the errors above.\n")
        return 1


if __name__ == "__main__":
    exit(main())
