import os
import sys

# Add parent directory to path to allow imports from main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import requests
from pymongo import MongoClient

def verify_full_deployment():
    """Verify all components of the deployment"""
    load_dotenv()
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    app_url = f"https://{project_id}.uc.r.appspot.com"
    
    print("\n=== Deployment Verification ===")
    
    # 1. Check web app
    print("\nChecking web application...")
    try:
        response = requests.get(app_url)
        print(f"App Status: {'✅' if response.status_code == 200 else '❌'} ({response.status_code})")
    except Exception as e:
        print(f"App Error: {str(e)}")

    # 2. Check MongoDB connection
    print("\nVerifying MongoDB connection...")
    try:
        client = MongoClient(os.getenv('MONGODB_URI'))
        db = client[os.getenv('MONGODB_DB_NAME')]
        db.command('ping')
        print("MongoDB Connection: ✅")
    except Exception as e:
        print(f"MongoDB Error: {str(e)}")

    # 3. Check webhook endpoint with proper parameters
    print("\nTesting webhook endpoint...")
    try:
        webhook_token = os.getenv('WHATSAPP_WEBHOOK_TOKEN')
        webhook_url = f"{app_url}/webhook?hub.mode=subscribe&hub.verify_token={webhook_token}&hub.challenge=test_challenge"
        webhook_response = requests.get(webhook_url)
        print(f"Webhook Status: {'✅' if webhook_response.status_code == 200 else '❌'} ({webhook_response.status_code})")
        print(f"Webhook Response: {webhook_response.text}")
    except Exception as e:
        print(f"Webhook Error: {str(e)}")

if __name__ == "__main__":
    verify_full_deployment()
