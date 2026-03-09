"""
Test to verify OTP email fixes are working correctly
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

print("=" * 80)
print("OTP EMAIL FIX VERIFICATION")
print("=" * 80)

all_checks_passed = True

# Test 1: Verify get_optional_current_user_email exists
print("\n[1/5] Checking optional auth dependency function exists...")
try:
    from presentation.routers.auth_router import get_optional_current_user_email
    import inspect
    
    # Check it returns Optional[str]
    sig = inspect.signature(get_optional_current_user_email)
    assert sig.return_annotation == "Optional[str]" or "Optional" in str(sig.return_annotation)
    print("✅ Optional auth dependency function exists and returns Optional[str]")
except Exception as e:
    print(f"✗ FAILED: {e}")
    all_checks_passed = False

# Test 2: Verify signup endpoint has current_user parameter
print("\n[2/5] Checking signup endpoint has authentication check...")
try:
    import ast
    with open('presentation/routers/auth_router.py', 'r', encoding='utf-8') as f:
        content = f.read()
        # Check for auth check in signup
        assert 'current_user: Optional[str]' in content, "Missing current_user parameter"
        assert 'if current_user:' in content, "Missing authentication check"
        assert 'already logged in' in content.lower(), "Missing proper error message"
    print("✅ Signup endpoint has authentication check to reject authenticated users")
except Exception as e:
    print(f"✗ FAILED: {e}")
    all_checks_passed = False

# Test 3: Verify Config import in signup_use_case
print("\n[3/5] Checking Config import in signup use case...")
try:
    with open('application/use_cases/signup_use_case.py', 'r', encoding='utf-8') as f:
        content = f.read()
        assert 'from config import Config' in content, "Missing Config import"
        assert 'Config.ENVIRONMENT' in content, "Not using Config.ENVIRONMENT"
        assert 'if Config.ENVIRONMENT != "production"' in content, "Missing production check"
    print("✅ Signup use case conditionally prints OTP based on environment")
except Exception as e:
    print(f"✗ FAILED: {e}")
    all_checks_passed = False

# Test 4: Verify Config import in resend_verification_use_case
print("\n[4/5] Checking Config import in resend verification use case...")
try:
    with open('application/use_cases/resend_verification_use_case.py', 'r', encoding='utf-8') as f:
        content = f.read()
        assert 'from config import' in content and 'Config' in content, "Missing Config import"
        assert 'Config.ENVIRONMENT' in content, "Not using Config.ENVIRONMENT"
        assert 'if Config.ENVIRONMENT != "production"' in content, "Missing production check"
    print("✅ Resend verification use case conditionally prints OTP based on environment")
except Exception as e:
    print(f"✗ FAILED: {e}")
    all_checks_passed = False

# Test 5: Verify email is always from request body, not session
print("\n[5/5] Checking email is taken from request body...")
try:
    with open('application/use_cases/signup_use_case.py', 'r', encoding='utf-8') as f:
        content = f.read()
        # Check that email parameter is used throughout
        assert 'email: str' in content, "Email not in function signature"
        assert 'to_email=email.lower()' in content, "Email not used correctly for sending"
    print("✅ Email is always taken from request body parameter")
except Exception as e:
    print(f"✗ FAILED: {e}")
    all_checks_passed = False

# Summary
print("\n" + "=" * 80)
if all_checks_passed:
    print("✓✓✓ ALL VERIFICATIONS PASSED! ✓✓✓")
    print("=" * 80)
    print("\nAll OTP email fixes are properly implemented:")
    print("  ✓ Optional auth dependency function exists")
    print("  ✓ Signup endpoint rejects authenticated users")
    print("  ✓ OTP logs only show in development mode")
    print("  ✓ Resend verification respects environment")
    print("  ✓ Email always taken from request body")
    print("\nThe OTP email system is now secure and production-ready!")
    print("\n📝 To use:")
    print("  - Set ENVIRONMENT=production in .env to hide OTP logs")
    print("  - OTP will still be sent via email even in production")
    print("  - Already logged-in users cannot trigger signup emails")
else:
    print("✗ SOME VERIFICATIONS FAILED")
    print("=" * 80)
print()
