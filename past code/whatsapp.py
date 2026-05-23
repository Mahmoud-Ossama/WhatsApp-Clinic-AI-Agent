import os
import requests
from datetime import datetime
import logging
from .message_templates import get_template_message

logger = logging.getLogger(__name__)

# Update API URL to latest version
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"

# Add debug header for better error information
WHATSAPP_HEADERS = {
    "Authorization": f"Bearer {os.getenv('WHATSAPP_API_TOKEN')}",
    "Content-Type": "application/json",
    "X-Meta-Debug": "true"  # Enable detailed error messages
}

INITIAL_MESSAGES = {
    'arab': """مرحباً! تم تسجيل بياناتك بنجاح في عيادة الدكتور وسيم.
تم تسجيل حقنتك، نتمنى لك الشفاء العاجل.
سنقوم بالتواصل معك بعد يومين للاطمئنان على حالتك.""",
    
    'israeli': """!שלום! הפרטים שלך נרשמו בהצלחה במרפאת ד"ר וסים
הזריקה שלך נרשמה, אנו מאחלים לך החלמה מהירה.
ניצור איתך קשר בעוד יומיים כדי לבדוק את מצבך."""
}

FOLLOWUP_MESSAGES = {
    'arab': """مرحباً! كيف حالك اليوم بعد يومين من الحقنة؟
1. جيد جداً 😊
2. جيد 🙂
3. لا تغيير 😐
4. سيء 😕
5. سيء جداً 😣""",
    
    'israeli': """!שלום! איך אתה מרגיש היום, יומיים אחרי הזריקה?
1. מצוין 😊
2. טוב 🙂
3. ללא שינוי 😐
4. לא טוב 😕
5. רע מאוד 😣"""
}

def send_immediate_message(phone, nationality='arab'):
    """Send immediate message after injection"""
    message = INITIAL_MESSAGES.get(nationality, INITIAL_MESSAGES['arab'])
    return send_message(phone, message)

def send_followup_message(phone, nationality='arab', next_appointment=None):
    """Send follow-up message with template fallback"""
    try:
        # First try regular message
        try:
            return send_message(phone, FOLLOWUP_MESSAGES.get(nationality, FOLLOWUP_MESSAGES['arab']))
        except Exception as e:
            if "131047" in str(e):  # 24h window error code
                logger.info(f"Falling back to template message for {phone}")
                # Use template message as fallback
                return send_template_message(
                    phone=phone,
                    template_name="followup_status_check",
                    language=nationality
                )
            raise
    except Exception as e:
        logger.error(f"Error in follow-up message flow: {e}")
        raise

def send_message(phone, message):
    """Generic message sending function"""
    try:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "text",
            "text": {"body": message}
        }

        response = requests.post(
            WHATSAPP_API_URL,
            headers=WHATSAPP_HEADERS,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise

def send_template_message(phone, template_name, language='ar', patient_name=None):
    """Send a WhatsApp template message that works outside 24h window"""
    try:
        # Get API configuration from environment
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        api_token = os.getenv('WHATSAPP_API_TOKEN')

        # Build the API URL with the phone number ID
        api_url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"

        logger.debug(f"Using Phone Number ID: {phone_number_id}")
        logger.debug(f"API URL: {api_url}")

        # Prepare headers with the token
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "ar" if language == 'arab' else "he"
                }
            }
        }

        logger.debug(f"Sending template message to {phone} with payload: {payload}")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        response_data = response.json()
        logger.debug(f"Template message response: {response_data}")

        if response.status_code != 200:
            error_data = response_data.get('error', {})
            error_message = error_data.get('message', 'Unknown error')
            error_code = error_data.get('code', 'N/A')
            raise Exception(f"WhatsApp API Error: {error_message} (Code: {error_code})")

        logger.info(f"Template message sent successfully to {phone}")
        return response_data

    except Exception as e:
        logger.error(f"Error sending template message: {e}")
        raise

def create_whatsapp_button_message(to_number, header_text, body_text, options):
    """Create a WhatsApp message with interactive buttons"""
    # WhatsApp limits: max 3 buttons
    buttons = []
    for i, opt in enumerate(options[:3]):  # Limit to first 3 options
        # Ensure button title is not too long (20 chars max)
        title = opt[:20] if len(opt) > 20 else opt
        buttons.append({"type": "reply", "reply": {"id": f"btn_{i}", "title": title}})
    
    # WhatsApp limits: header text max 60 chars
    header = header_text[:60] if header_text else "Dr. Wasim Clinic"
    
    # WhatsApp limits: body text max 1024 chars
    body = body_text[:1024] if body_text else "Please select an option:"
    
    # Add remaining options as text in the body if more than 3
    if len(options) > 3:
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options[3:])])
        body_suffix = f"\n\nAdditional options:\n{options_text}"
        
        # Make sure body with options doesn't exceed limit
        if len(body) + len(body_suffix) <= 1024:
            body += body_suffix
    
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": header
            },
            "body": {
                "text": body
            },
            "action": {
                "buttons": buttons
            }
        }
    }

def send_whatsapp_message(to_number, message_text, options=None):
    """Send message using WhatsApp Cloud API with button support"""
    try:
        to_number = to_number.replace('whatsapp:', '').strip()
        logger.debug(f"Preparing message for {to_number}")
        
        if options and len(options) > 0:
            # Create a simple text-only message with no header
            # This approach works better with Arabic text
            simple_payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_number,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {
                        "text": message_text  # Use full text in body only
                    },
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {  # Fixed typo here ("reply" not "repply")
                                    "id": f"btn_{i}",
                                    "title": opt[:20]  # WhatsApp limit
                                }
                            } 
                            for i, opt in enumerate(options[:3])
                        ]
                    }
                }
            }
            
            logger.debug(f"Using simple button format without header")
            response = requests.post(
                WHATSAPP_API_URL,
                headers=WHATSAPP_HEADERS,
                json=simple_payload,
                timeout=10
            )
        else:
            # Simple text message - always reliable
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_number,
                "type": "text",
                "text": {"body": message_text}
            }
            
            response = requests.post(
                WHATSAPP_API_URL,
                headers=WHATSAPP_HEADERS,
                json=payload,
                timeout=10
            )
        
        # Handle response
        if response.status_code != 200:
            error_details = response.json().get('error', {})
            logger.error(f"WhatsApp API error: {error_details.get('message')} (Code: {error_details.get('code', 'Unknown')})")
            logger.error(f"Full response: {response.text}")
            raise Exception(f"WhatsApp API error: {response.text}")
        
        response_data = response.json()
        logger.debug(f"WhatsApp API success: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"WhatsApp message error: {str(e)}")
        # Fall back to plain text with options as text
        try:
            options_text = ""
            if options:
                options_text = "\n\n" + "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
            
            text_payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_number,
                "type": "text",
                "text": {"body": message_text + options_text}
            }
            
            logger.info(f"Using plain text fallback")
            return requests.post(WHATSAPP_API_URL, headers=WHATSAPP_HEADERS, json=text_payload).json()
        except:
            logger.error("Even fallback message failed")
            raise
