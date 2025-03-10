import requests
import os
from dotenv import load_dotenv

def test_webhook_availability():
    """Test if the webhook is available and working properly"""
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    webhook_token = os.getenv('WHATSAPP_WEBHOOK_TOKEN')
    app_url = f"https://{project_id}.uc.r.appspot.com"
    
    print(f"\nTesting deployment at {app_url}")
    
    # Test 1: Root endpoint
    try:
        print("\n1. Testing root endpoint...")
        response = requests.get(app_url)
        print(f"Status: {'✅' if response.status_code == 200 else '❌'} ({response.status_code})")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test 2: Webhook endpoint without parameters
    try:
        print("\n2. Testing webhook endpoint without parameters...")
        response = requests.get(f"{app_url}/webhook")
        print(f"Status: {'✅' if response.status_code == 200 else '❌'} ({response.status_code})")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test 3: Webhook with correct verification parameters
    try:
        print("\n3. Testing webhook verification with correct token...")
        test_url = f"{app_url}/webhook?hub.mode=subscribe&hub.verify_token={webhook_token}&hub.challenge=test_challenge"
        response = requests.get(test_url)
        print(f"Status: {'✅' if response.status_code == 200 else '❌'} ({response.status_code})")
        print(f"Response: {response.text}")
        print(f"Expected: test_challenge")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test 4: Webhook with incorrect token
    try:
        print("\n4. Testing webhook verification with incorrect token...")
        test_url = f"{app_url}/webhook?hub.mode=subscribe&hub.verify_token=wrong_token&hub.challenge=test_challenge"
        response = requests.get(test_url)
        print(f"Status: {'✅' if response.status_code == 403 else '❌'} ({response.status_code})")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_webhook_availability()
