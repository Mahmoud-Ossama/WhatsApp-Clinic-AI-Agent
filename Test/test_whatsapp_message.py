import os
import sys

# Add parent directory to path to allow imports from main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

def send_test_message(phone_number):
    """Send a test message with different formats to diagnose issues"""
    
    # API configuration
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    api_token = os.getenv('WHATSAPP_API_TOKEN')
    api_url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Simple text message
    text_payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": "اختبار رسالة بسيطة من عيادة د. وسيم"
        }
    }
    
    # Test 2: Interactive button message (simplest form)
    button_payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "مرحباً بك في عيادة د. وسيم العبرة. كيف يمكنني مساعدتك؟"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "btn_1",
                            "title": "حجز موعد"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "btn_2", 
                            "title": "معلومات عن العيادة"
                        }
                    }
                ]
            }
        }
    }
    
    # Test 3: Template message
    template_payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "welcome_message",
            "language": {
                "code": "ar"
            }
        }
    }
    
    # Send and test responses
    print("\n===== TESTING WHATSAPP MESSAGES =====\n")
    
    print("1. Sending simple text message...")
    response = requests.post(api_url, headers=headers, json=text_payload)
    print(f"Response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    print("\n2. Sending button message...")
    response = requests.post(api_url, headers=headers, json=button_payload)
    print(f"Response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    print("\n3. Sending template message...")
    response = requests.post(api_url, headers=headers, json=template_payload)
    print(f"Response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    phone = input("Enter phone number (with country code, e.g. 201003169833): ")
    send_test_message(phone)
