"""
Test script for consultation booking endpoint
"""
import asyncio
import httpx


async def test_consultation_submission():
    """Test the consultation submission endpoint"""
    
    base_url = "http://localhost:8000"
    
    # Test valid submission
    print("Testing valid consultation submission...")
    valid_data = {
        "first_name": "John",
        "last_name": "Doe",
        "business_email": "john.doe@example.com",
        "company_name": "Acme Corp"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/api/consultation/submit",
                json=valid_data
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
    
    # Test duplicate submission (should get 409)
    print("Testing duplicate submission...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/api/consultation/submit",
                json=valid_data
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
    
    # Test invalid email
    print("Testing invalid email...")
    invalid_email_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "business_email": "not-an-email",
        "company_name": "Test Inc"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/api/consultation/submit",
                json=invalid_email_data
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
    
    # Test missing fields
    print("Testing missing fields...")
    incomplete_data = {
        "first_name": "Bob",
        "business_email": "bob@test.com"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/api/consultation/submit",
                json=incomplete_data
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
    
    # Test XSS attempt
    print("Testing XSS sanitization...")
    xss_data = {
        "first_name": "<script>alert('xss')</script>John",
        "last_name": "Doe{test}",
        "business_email": "xss-test@example.com",
        "company_name": "Test$Corp"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{base_url}/api/consultation/submit",
                json=xss_data
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
    
    # Test rate limiting (5 requests in quick succession)
    print("Testing rate limiting (sending 6 requests quickly)...")
    rate_limit_data = {
        "first_name": "Rate",
        "last_name": "Test",
        "business_email": f"ratetest{{i}}@example.com",
        "company_name": "Rate Corp"
    }
    
    async with httpx.AsyncClient() as client:
        for i in range(6):
            rate_limit_data["business_email"] = f"ratetest{i}@example.com"
            try:
                response = await client.post(
                    f"{base_url}/api/consultation/submit",
                    json=rate_limit_data
                )
                print(f"Request {i+1} - Status: {response.status_code}")
                if response.status_code == 429:
                    print(f"Rate limited! Response: {response.text}")
            except Exception as e:
                print(f"Request {i+1} - Error: {e}")
            await asyncio.sleep(0.5)  # Small delay between requests


if __name__ == "__main__":
    asyncio.run(test_consultation_submission())
