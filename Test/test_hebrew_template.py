import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from utils.whatsapp import send_template_message

load_dotenv()

def test_hebrew_template():
    """Test sending a Hebrew template message"""
    phone_number = input("Enter phone number to test (with country code): ")
    
    print("Sending Hebrew template message...")
    response = send_template_message(
        phone=phone_number,
        template_name="welcome_message",  # Use your actual template name
        language="he"  # Hebrew language code
    )
    
    print(f"Response: {response}")
    
if __name__ == "__main__":
    test_hebrew_template()
