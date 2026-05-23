import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

def test_hebrew_message():
    """Send a test Hebrew message directly to the deployed webhook"""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    webhook_url = f"https://{project_id}.uc.r.appspot.com/webhook"
    
    # Sample Hebrew WhatsApp message webhook payload
    test_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "12345",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "972549585797",
                        "phone_number_id": os.getenv('WHATSAPP_PHONE_NUMBER_ID')
                    },
                    "messages": [{
                        "from": "201003169833",  # Replace with test number
                        "id": "wamid.test123",
                        "timestamp": "1611247511",
                        "type": "text",
                        "text": {
                            "body": "שלום, איך אני יכול לקבוע תור?"  # Hello, how can I make an appointment?
                        }
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    print("Sending test Hebrew message to webhook...")
    
    try:
        response = requests.post(webhook_url, json=test_payload)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        print("\nCheck your logs for 'HEBREW DETECTED' and language codes.")
        print("Run: gcloud app logs tail")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_hebrew_message()
