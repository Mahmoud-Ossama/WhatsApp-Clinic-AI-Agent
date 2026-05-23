import os
import logging
import requests
from datetime import datetime, timedelta

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

def send_whatsapp_message(recipient_id, message_text):
    """Send a simple text WhatsApp message"""
    try:
        # Sanitize message text
        if isinstance(message_text, str):
            message_text = message_text.replace('"', "'").strip()
        else:
            message_text = str(message_text)
        
        # Ensure message isn't too long
        if len(message_text) > 4096:  # WhatsApp's hard limit
            message_text = message_text[:4093] + "..."
        
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': recipient_id,
            'type': 'text',
            'text': {'body': message_text}
        }
        
        logger.debug(f"Sending WhatsApp message - Payload: {payload}")
        response = requests.post(
            WHATSAPP_API_URL,
            headers=WHATSAPP_HEADERS,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 401:
            logger.error("WhatsApp API authentication failed. Please check your API token.")
            raise Exception("WhatsApp API authentication failed")
            
        response.raise_for_status()
        response_data = response.json()
        logger.debug(f"WhatsApp API response: {response_data}")
        return response_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp API request failed: {str(e)}")
        raise

def send_whatsapp_interactive(recipient_id, response):
    """Send an interactive WhatsApp message with buttons"""
    try:
        # Extract text and options from the response
        text = response.get('text', '')
        options = response.get('options', [])
        
        if not text:
            logger.warning("Empty response text, cannot send interactive message")
            return
        
        # Sanitize the text to avoid special character issues
        text = text.replace('"', "'").strip()
        
        # Check for too complex message conditions
        is_too_complex = (
            len(text) > 1000 or  # Very long text
            len(options) > 3 or  # Too many buttons
            any(len(opt) > 20 for opt in options)  # Button text too long
        )
        
        if is_too_complex:
            # Fall back to simple text message format
            send_whatsapp_message(recipient_id=recipient_id, message_text=text)
            
            # If we had options, send them as a separate simple message
            if options:
                options_text = "אפשרויות:\n" + "\n".join([f"• {opt}" for opt in options])
                send_whatsapp_message(recipient_id=recipient_id, message_text=options_text)
            return
        
        # Prepare header (max 60 chars)
        header_text = text[:60] if len(text) > 60 else text
        
        # Prepare the interactive message
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': recipient_id,
            'type': 'interactive',
            'interactive': {
                'type': 'button',
                'header': {
                    'type': 'text',
                    'text': header_text
                },
                'body': {
                    'text': text
                },
                'action': {
                    'buttons': [
                        {
                            'type': 'reply',
                            'reply': {
                                'id': f'btn_{i}',
                                'title': opt[:20]  # Ensure buttons respect 20-char limit
                            }
                        } for i, opt in enumerate(options[:3])  # Max 3 buttons
                    ]
                }
            }
        }
        
        # Send the request
        logger.debug(f"Sending WhatsApp interactive message - Payload: {payload}")
        response = requests.post(
            WHATSAPP_API_URL,
            headers=WHATSAPP_HEADERS,
            json=payload
        )
        
        if response.status_code != 200:
            logger.error(f"WhatsApp API request failed: {response.status_code} {response.reason}")
            # Fall back to simple text message
            send_whatsapp_message(recipient_id=recipient_id, message_text=text)
        else:
            logger.debug(f"WhatsApp API response: {response.json()}")
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp interactive message: {str(e)}")
        # Try to send the text as a simple message
        if 'text' in locals():
            send_whatsapp_message(recipient_id=recipient_id, message_text=text)

def send_immediate_message(phone, nationality='arab'):
    """Send immediate message after injection"""
    message = INITIAL_MESSAGES.get(nationality, INITIAL_MESSAGES['arab'])
    return send_whatsapp_message(phone, message)

def send_followup_message(phone, nationality='arab', next_appointment=None):
    """Send follow-up message with template fallback"""
    try:
        # First try regular message
        try:
            return send_whatsapp_message(phone, FOLLOWUP_MESSAGES.get(nationality, FOLLOWUP_MESSAGES['arab']))
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

def send_template_message(phone, template_name, params=None, language='ar'):
    """Send a WhatsApp template message that works outside 24h window"""
    try:
        # Map internal language codes to WhatsApp language codes
        lang_map = {
            'arab': 'ar',
            'israeli': 'he', 
            'ar': 'ar',
            'he': 'he',
            'en': 'en_US'
        }
        
        # Get proper language code
        whatsapp_lang = lang_map.get(language, 'ar')
        
        # Create payload
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": whatsapp_lang
                }
            }
        }
        
        # Add parameters if provided
        if params:
            components = []
            if isinstance(params, list):
                components.append({
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(p)} for p in params]
                })
            elif isinstance(params, dict):
                components.append({
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(v)} for v in params.values()]
                })
            
            if components:
                payload["template"]["components"] = components
        
        # Send request
        response = requests.post(
            WHATSAPP_API_URL,
            headers=WHATSAPP_HEADERS,
            json=payload
        )
        
        response.raise_for_status()
        return response.json()
            
    except Exception as e:
        logger.error(f"Error sending template message: {str(e)}")
        raise

def process_scheduled_messages():
    """Process any scheduled messages that need to be sent"""
    try:
        from dashboard.models import db
        now = datetime.utcnow()
        
        # Find messages scheduled for sending
        scheduled_msgs = db.scheduled_messages.find({
            'status': 'scheduled',
            'scheduled_date': {'$lte': now}
        })
        
        count = 0
        for msg in scheduled_msgs:
            try:
                phone = msg.get('phone')
                text = msg.get('text')
                msg_type = msg.get('type', 'text')
                
                # Send the message based on type
                if msg_type == 'followup':
                    nationality = msg.get('nationality', 'arab')
                    result = send_followup_message(phone, nationality)
                else:
                    # Default to regular text message
                    result = send_whatsapp_message(phone, text)
                
                # Update status in database
                db.scheduled_messages.update_one(
                    {'_id': msg['_id']},
                    {'$set': {
                        'status': 'sent',
                        'sent_date': now,
                        'result': str(result)
                    }}
                )
                
                count += 1
                logger.info(f"Sent scheduled message to {phone}")
                
            except Exception as send_error:
                logger.error(f"Failed to send scheduled message to {msg.get('phone')}: {str(send_error)}")
                # Mark as failed in database
                db.scheduled_messages.update_one(
                    {'_id': msg['_id']},
                    {'$set': {
                        'status': 'failed',
                        'error': str(send_error),
                        'last_attempt': now
                    }}
                )
        
        return count
    except Exception as e:
        logger.error(f"Error in process_scheduled_messages: {str(e)}")
        return 0

def schedule_message(phone, text, scheduled_date, message_type='scheduled', patient_id=None, patient_name=None, nationality='arab'):
    """Schedule a message to be sent later"""
    try:
        from dashboard.models import db
        
        # Create the message document
        message_doc = {
            'phone': phone,
            'text': text,
            'scheduled_date': scheduled_date,
            'status': 'scheduled',
            'type': message_type,
            'created_date': datetime.utcnow(),
            'nationality': nationality
        }
        
        # Add optional fields if present
        if patient_id:
            message_doc['patient_id'] = patient_id
        if patient_name:
            message_doc['patient_name'] = patient_name
            
        # Insert into database
        result = db.scheduled_messages.insert_one(message_doc)
        logger.info(f"Scheduled message for {phone} on {scheduled_date}")
        
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error scheduling message: {str(e)}")
        raise

def schedule_injection_followup(patient_id, phone, patient_name, nationality, delay_days=2):
    """Schedule a follow-up message for an injection patient"""
    try:
        # Calculate the date for the follow-up (default 2 days later)
        followup_date = datetime.utcnow() + timedelta(days=delay_days)
        
        # Schedule the follow-up message
        result = schedule_message(
            phone=phone,
            text="",  # Will use template text based on nationality
            scheduled_date=followup_date,
            message_type='followup',
            patient_id=patient_id,
            patient_name=patient_name,
            nationality=nationality
        )
        
        logger.info(f"Scheduled injection follow-up for patient {patient_id} on {followup_date}")
        return result
    except Exception as e:
        logger.error(f"Error scheduling injection follow-up: {str(e)}")
        raise
