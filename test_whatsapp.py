from utils.whatsapp import send_template_message
import logging
from dotenv import load_dotenv
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def verify_env():
    """Verify all required environment variables are set and valid"""
    required_vars = [
        'WHATSAPP_API_TOKEN',
        'WHATSAPP_PHONE_NUMBER_ID'
    ]
    
    errors = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            errors.append(f"Missing {var}")
        elif var == 'WHATSAPP_API_TOKEN' and len(value) < 100:
            errors.append(f"Invalid {var} - token seems too short")
        elif var == 'WHATSAPP_PHONE_NUMBER_ID' and not value.isdigit():
            errors.append(f"Invalid {var} - should be numeric")

    if errors:
        print("\nEnvironment variable errors:")
        for error in errors:
            print(f"- {error}")
        return False
    return True

def test_template():
    try:
        # Test phone number (replace with your test number)
        phone_number = "201003169833"

        # Log configuration
        print("\nTesting WhatsApp Configuration:")
        print(f"Phone Number ID: {os.getenv('WHATSAPP_PHONE_NUMBER_ID')}")
        print(f"Target Phone: {phone_number}")
        print(f"Template Name: followup_status_check")
        print("\nSending message...")
        
        response = send_template_message(
            phone=phone_number,
            template_name="followup_status_check",
            language="arab"
        )
        
        print("\nSuccess!")
        print(f"Message ID: {response.get('messages', [{}])[0].get('id', 'N/A')}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        logger.exception("Detailed error:")

if __name__ == "__main__":
    if verify_env():
        test_template()
    else:
        print("\nPlease fix environment variables before testing")
