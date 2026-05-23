import atexit
import sys
from werkzeug.security import check_password_hash
from flask import flash
from flask_login import login_user
from flask import Flask, request, redirect, url_for, render_template
import requests
from google.cloud.dialogflowcx_v3beta1 import SessionsClient
from google.cloud.dialogflowcx_v3beta1.types import TextInput, QueryInput, QueryParameters, EventInput
from google.oauth2 import service_account
import os
import logging
from dotenv import load_dotenv
from google.api_core import client_options
from flask_admin import Admin
from flask_login import LoginManager, login_required, logout_user
from dashboard.models import User, Patient, Injection, FollowUp, db  # Add db to imports
from dashboard.views import AdminModelView, PatientView, FollowUpView, PatientResponseView, MessageHistoryView, DashboardView as AdminDashboardView  # Updated import
from utils.scheduler import init_scheduler
from datetime import datetime, timedelta
import re  # Add regex module for language detection functions
from utils.dialogflow_client import detect_intent_texts as process_arabic_text, trigger_dialogflow_event
from custom_nlp.flow_manager import process_hebrew_flow

# Import our enhanced logging configuration
from logging_config import setup_logging

# Set up enhanced logging with error handling
try:
    logger = setup_logging(app_name="dr_wasim", log_level=logging.DEBUG)
except Exception as e:
    # If setup_logging fails, set up a basic console logger
    print(f"Error setting up logging: {str(e)}. Using basic console logging.")
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger(__name__)

load_dotenv()

# WhatsApp API Configuration
WHATSAPP_API_URL = f"https://graph.facebook.com/v17.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"
WHATSAPP_HEADERS = {
    "Authorization": f"Bearer {os.getenv('WHATSAPP_API_TOKEN')}",
    "Content-Type": "application/json"
}

# Setup Google Cloud credentials
try:
    SERVICE_ACCOUNT_FILE = 'service_account.json'
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file '{SERVICE_ACCOUNT_FILE}' not found")
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    logger.debug("Successfully loaded service account credentials")

    # Configure client options with regional endpoint
    client_options_obj = client_options.ClientOptions(
        api_endpoint=f"{os.getenv('DIALOGFLOW_LOCATION')}-dialogflow.googleapis.com"
    )
    
    # Initialize Dialogflow CX beta client with credentials and regional endpoint
    dialogflow_client = SessionsClient(
        credentials=credentials,
        client_options=client_options_obj
    )
    
    agent_path = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}/locations/{os.getenv('DIALOGFLOW_LOCATION')}/agents/{os.getenv('DIALOGFLOW_AGENT_ID')}"
    logger.debug(f"Initialized Dialogflow client with agent path: {agent_path}")
except Exception as e:
    logger.error(f"Failed to initialize: {str(e)}")
    raise

app = Flask(__name__, 
           template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Initialize Flask-Admin with custom dashboard view
admin = Admin(app, 
             name='عيادة د. وسيم',
             template_mode='bootstrap4',
             url='/dashboard',
             index_view=AdminDashboardView())  # Use the imported class

# Add views including the new Patient Response view
admin.add_view(PatientView(db.patients, 'المرضى', endpoint='patient_admin'))
admin.add_view(FollowUpView(db.followups, 'المتابعات', endpoint='followup_admin'))
admin.add_view(PatientResponseView(name='ردود المرضى', endpoint='response_admin'))
admin.add_view(MessageHistoryView(name='سجل الرسائل', endpoint='message_history'))

# Initialize the scheduler
scheduler = init_scheduler()

# Add cleanup on app shutdown
@atexit.register
def shutdown_scheduler():
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler shut down")

def create_whatsapp_button_message(to_number, header_text, body_text, options):
    """Create a WhatsApp message with interactive buttons"""
    # WhatsApp limits: max 3 buttons
    buttons = [{"type": "reply", "reply": {"id": f"btn_{i}", "title": opt}} 
              for i, opt in enumerate(options[:3])]  # Limit to first 3 options
    
    # Use first sentence as header (max 60 chars) and rest as body
    header_parts = header_text.split('.')
    header = (header_parts[0] + '.').strip()[:60]
    
    # Combine remaining text as body
    remaining_text = '.'.join(header_parts[1:]).strip()
    if (remaining_text):
        body_text = remaining_text + "\n\n" + body_text if body_text else remaining_text
    
    # Ensure body is not empty
    if not body_text.strip():
        body_text = header
    
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
                "text": body_text
            },
            "action": {
                "buttons": buttons
            }
        }
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
        
        # 1. Determine if the message is too complex for interactive format
        is_too_complex = (
            len(text) > 1000 or  # Very long text
            len(options) > 3 or  # Too many buttons
            any(len(opt) > 20 for opt in options)  # Button text too long
        )
        
        # 2. Handle post-injection message specifically (common failure case)
        is_post_injection = (
            response.get('detected_intent') == "post_injection" or
            "כאב לאחר הזרקה" in text or
            "תופעות לוואי" in text
        )
        
        # 3. If message is too complex or is a post-injection message, use simplified format
        if is_too_complex or is_post_injection:
            # For post-injection guidance, prefer text-only format which is more reliable
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
                                'title': opt
                            }
                        } for i, opt in enumerate(options[:3])  # Max 3 buttons
                    ]
                }
            }
        }
        
        # Send the request
        logger.debug(f"Sending WhatsApp message - Payload: {payload}")
        response = requests.post(
            f"https://graph.facebook.com/v17.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages",
            headers={
                "Authorization": f"Bearer {os.getenv('WHATSAPP_API_TOKEN')}",
                "Content-Type": "application/json"
            },
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

def send_fallback_message(recipient_id, language='he'):
    """Send a guaranteed-to-work fallback message"""
    try:
        # Use simple text that will definitely work
        if language == 'he':
            message = "סליחה, נתקלנו בבעיה טכנית. אנא נסה שוב או צור קשר עם המרפאה בטלפון 0537330702."
        else:
            message = "عذراً، هناك مشكلة فنية. الرجاء المحاولة مرة أخرى على الرقم 0537330702."
        
        # Send a direct message that doesn't depend on other functions
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': recipient_id,
            'type': 'text',
            'text': {'body': message}
        }
        
        requests.post(
            f"https://graph.facebook.com/v17.0/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages",
            headers={
                "Authorization": f"Bearer {os.getenv('WHATSAPP_API_TOKEN')}",
                "Content-Type": "application/json"
            },
            json=payload
        )
            
    except Exception as e:
        logger.error(f"Even fallback message failed: {str(e)}")

@app.route('/')
def home():
    return 'WhatsApp-Dialogflow Webhook is running!'

@app.route('/webhook', methods=['GET'])
def verify():
    """Handle webhook verification from WhatsApp Cloud API"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    logger.info(f"Webhook verification - Mode: {mode}, Token: {token}, Challenge: {challenge}")

    # Check if this is a direct browser access
    if not mode and not token and not challenge:
        return 'WhatsApp Webhook Endpoint - Please configure this URL in Meta Developer Portal with proper verification parameters', 200

    # Normal webhook verification
    if mode and token:
        if mode == 'subscribe' and token == os.getenv('WHATSAPP_WEBHOOK_TOKEN'):
            logger.info("Webhook verified successfully")
            return str(challenge), 200
        logger.error(f"Token mismatch. Received: {token}")
        return 'Invalid verification token', 403
    
    logger.warning(f"Missing required parameters. Mode: {mode}, Token present: {'Yes' if token else 'No'}")
    return 'Missing verification parameters', 400

def extract_response_text(response, detected_language=None):
    """Enhanced response text extraction with language-aware handling"""
    try:
        if not response.query_result.response_messages:
            return "No response available.", None

        messages = []
        options = []
        
        # If language not provided, get it from the response
        if detected_language is None:
            detected_language = response.query_result.language_code
        
        # Process all response messages
        for msg in response.query_result.response_messages:
            try:
                # Handle text messages
                if hasattr(msg, 'text') and msg.text.text:
                    messages.extend(msg.text.text)
                
                # Handle custom payload (richContent)
                elif hasattr(msg, 'payload'):
                    payload_dict = dict(msg.payload)
                    logger.debug(f"Found payload: {payload_dict}")
                    
                    # Extract richContent which contains the custom UI elements
                    rich_content = payload_dict.get('richContent', [])
                    
                    # richContent is a nested array [[...elements...]]
                    for content_group in rich_content:
                        for content in content_group:
                            content_type = content.get('type', '')
                            
                            # Handle description type
                            if content_type == 'description':
                                title = content.get('title', '')
                                text_list = content.get('text', [])
                                if title:
                                    messages.append(title)
                                messages.extend(text_list)
                            
                            # Handle chips/buttons type
                            elif content_type == 'chips':
                                # Extract option texts directly from the options array
                                opt_items = content.get('options', [])
                                for opt in opt_items:
                                    if 'text' in opt:
                                        options.append(opt['text'])
            except Exception as e:
                logger.error(f"Error processing message part: {str(e)}", exc_info=True)
                continue

        message_text = "\n\n".join(filter(None, messages))
        logger.debug(f"Extracted text: '{message_text[:100]}...' and {len(options)} options: {options}")
        
        # If no message text was extracted, use a fallback response
        if not message_text:
            if detected_language == "he":
                message_text = "מצטער, לא הבנתי. איך אוכל לעזור לך?"
            else:
                message_text = "آسف، لم أفهم. كيف يمكنني مساعدتك؟"
        
        return message_text, options if options else None
    except Exception as e:
        logger.error(f"Error extracting response text: {e}", exc_info=True)
        return "Sorry, I'm having trouble processing the response.", None

def should_reset_session(sender_phone):
    """Check if session should be reset based on last message time"""
    try:
        # Get last message timestamp from MongoDB
        last_message = db.message_history.find_one(
            {'phone': sender_phone},
            sort=[('timestamp', -1)]
        )
        
        if not last_message:
            return True

        # Check if more than 1 minute has passed
        last_time = last_message['timestamp']
        if datetime.utcnow() - last_time > timedelta(minutes=1):
            logger.info(f"Session timeout for {sender_phone}")
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error checking session timeout: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        logger.debug(f"Received webhook data: {data}")

        # Verify if it's a status update
        if 'entry' in data and 'changes' in data['entry'][0]:
            changes = data['entry'][0]['changes'][0]
            if 'value' in changes and 'statuses' in changes['value']:
                status_data = changes['value']['statuses'][0]
                message_id = status_data.get('id')
                status = status_data.get('status')
                timestamp = status_data.get('timestamp')
                
                logger.info(f"Message Status Update - ID: {message_id}, Status: {status}, Timestamp: {timestamp}")
                return 'OK', 200

        # Handle incoming messages
        if 'entry' in data and 'changes' in data['entry'][0]:
            changes = data['entry'][0]['changes'][0]
            if 'value' in changes and 'messages' in changes['value']:
                message = changes['value']['messages'][0]
                sender_id = message.get('from')
                message_text = message.get('text', {}).get('body', '') if message.get('type') == 'text' else ''
                
                logger.info(f"Processing message from {sender_id}: {message_text}")
                
                # Process the message
                process_message(message)
                
                return 'OK', 200
        
        return 'OK', 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        # Don't try to send a message if we don't have a sender_id
        if 'sender_id' in locals():
            try:
                send_fallback_message(recipient_id=sender_id, language='ar')
            except Exception as inner_e:
                logger.error(f"Failed to send fallback message: {str(inner_e)}")
        
        # Print the full stack trace for debugging
        import traceback
        logger.error(traceback.format_exc())
        return 'OK', 200

# Main message handling function
def process_message(message):
    """
    Process an incoming WhatsApp message and generate a response
    
    Args:
        message (dict): Message data from WhatsApp
    """
    try:
        # Extract sender ID and message text
        sender_id = message.get('from')
        message_type = message.get('type', 'text')
        
        # Initialize response variable to avoid the UnboundLocalError
        response = None
        
        # Handle different message types
        if message_type == 'interactive':
            # Handle button clicks
            logger.info(f"Processing interactive message from {sender_id}")
            
            # Extract button details
            button_response = message.get('interactive', {}).get('button_reply', {})
            button_id = button_response.get('id', '')
            button_title = button_response.get('title', '')
            
            logger.info(f"User {sender_id} clicked button: {button_title} (ID: {button_id})")
            
            # Check if it's an Arabic button
            if any(arabic_char in button_title for arabic_char in 'ءآأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوي'):
                logger.info(f"Processing Arabic button selection: {button_title}")
                
                # Create event input based on button ID/title
                event_name = None
                if "الخدمات" in button_title:
                    event_name = "services_selected"
                elif "حجز موعد" in button_title:
                    event_name = "appointment_selected"
                elif "دعم" in button_title and "العلاج" in button_title:
                    event_name = "support_selected"
                
                # If we have a mapped event, use it, otherwise fall back to text
                if event_name:
                    response = trigger_dialogflow_event(sender_id, event_name, language_code='ar')
                else:
                    # Fall back to text handling if no specific event mapping
                    response = process_arabic_text(button_title, sender_id)
                
            else:
                # Handle Hebrew or English buttons
                # [Your existing code for non-Arabic buttons]
                pass
            
        elif message_type == 'text':
            # Process normal text messages
            text = message.get('text', {}).get('body', '')
            
            # Process the text based on language
            if is_arabic(text):
                # Process Arabic text with Dialogflow
                logging.info(f"Routing Arabic text to Dialogflow: '{text[:30]}...'")
                dialogflow_response = process_arabic_text(text, sender_id)
                
                # Send response directly since Dialogflow handles this differently
                send_whatsapp_response(sender_id, dialogflow_response)
                
                # No need to return response again
                return
                
            # Hebrew text processing through our flow system
            elif is_hebrew(text):
                # Process Hebrew text with our NLP system
                logging.info(f"🔍 HE DETECTED: '{text[:30]}...' - Using language 'he'")
                show_character_codes(text[:20])
                
                # Use the flow manager to process the message
                response = process_hebrew_flow(text, sender_id)
                
            # Default to English processing
            else:
                # For English, use a simpler approach
                logging.info(f"🔍 EN DETECTED: '{text[:30]}...' - Using language 'en'")
                response = {
                    "text": "I'm sorry, I currently only support Hebrew and Arabic. Please use one of these languages.",
                    "options": []
                }
                
        elif message_type == 'button':
            # Handle button replies
            button_payload = message.get('button', {}).get('payload', '')
            button_text = message.get('button', {}).get('text', '')
            
            # Process button click as if it was a text message
            process_message({
                'from': sender_id,
                'id': message.get('id'),
                'timestamp': message.get('timestamp'),
                'type': 'text',
                'text': {'body': button_text}
            })
        
        elif message_type == 'interactive':
            # Handle interactive message responses
            interactive_data = message.get('interactive', {})
            interactive_type = interactive_data.get('type', '')
            
            if interactive_type == 'button_reply':
                button_reply = interactive_data.get('button_reply', {})
                button_id = button_reply.get('id', '')
                button_title = button_reply.get('title', '')
                
                # Process button click as if it was a text message
                process_message({
                    'from': sender_id,
                    'id': message.get('id'),
                    'timestamp': message.get('timestamp'),
                    'type': 'text',
                    'text': {'body': button_title}
                })
            
            elif interactive_type == 'list_reply':
                list_reply = interactive_data.get('list_reply', {})
                list_id = list_reply.get('id', '')
                list_title = list_reply.get('title', '')
                
                # Process list selection as if it was a text message
                process_message({
                    'from': sender_id,
                    'id': message.get('id'),
                    'timestamp': message.get('timestamp'),
                    'type': 'text',
                    'text': {'body': list_title}
                })
    
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        # Send error response in both languages
        error_message = {
            "text": "Sorry, there was an error processing your message. Please try again.\n\nعذراً، هناك مشكلة فنية. الرجاء المحاولة مرة أخرى."
        }
        send_whatsapp_response(sender_id, error_message)

    # Only attempt to send response if it exists and has text
    if response and 'text' in response:
        send_whatsapp_response(sender_id, response)

@app.route('/dashboard')
@login_required
def admin_dashboard():
    return redirect(url_for('admin.index'))

# Add login routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_data = db.users.find_one({'username': username})
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(
                username=user_data['username'],
                password_hash=user_data['password_hash'],
                role=user_data.get('role', 'doctor')
            )
            user.id = str(user_data['_id'])
            login_user(user)
            return redirect(url_for('admin.index'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Import the tasks blueprint
from tasks import tasks_blueprint

# Register the tasks blueprint
app.register_blueprint(tasks_blueprint)

# Add these functions at the top of the file, after the imports

def is_arabic(text):
    """Check if text contains Arabic characters"""
    if not text:
        return False
    # Arabic Unicode range (0600-06FF)
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    return bool(arabic_pattern.search(text))

def is_hebrew(text):
    """Check if text contains Hebrew characters"""
    if not text:
        return False
    # Hebrew Unicode range (0590-05FF)
    hebrew_pattern = re.compile(r'[\u0590-\u05FF]')
    return bool(hebrew_pattern.search(text))

def show_character_codes(text):
    """Log the Unicode character codes for debugging"""
    if not text:
        return
    char_codes = ', '.join([f"{c}:{ord(c):x}" for c in text[:20]])
    logger.info(f"🔍 CHARACTER CODES: {char_codes}")

def send_whatsapp_response(recipient_id, response):
    """Send a WhatsApp response with proper error handling"""
    try:
        if not response:
            logger.warning(f"Empty response for recipient {recipient_id}")
            return
            
        logger.debug(f"Sending WhatsApp response for {recipient_id}: Text={response.get('text', '')[:50]}..., Options={response.get('options', [])}")
        
        # Send as interactive message with buttons if possible
        if 'options' in response and response['options']:
            is_complex = (
                len(response.get('text', '')) > 1000 or 
                len(response.get('options', [])) > 3 or
                any(len(opt) > 20 for opt in response.get('options', []))
            )
            
            if is_complex:
                # Send as split messages for complex responses
                send_whatsapp_message(recipient_id=recipient_id, message_text=response.get('text', ''))
                # Send options as a separate message
                options_text = "אפשרויות:\n" + "\n".join([f"• {opt}" for opt in response['options']])
                send_whatsapp_message(recipient_id=recipient_id, message_text=options_text)
            else:
                # Try interactive buttons
                try:
                    send_whatsapp_interactive(recipient_id=recipient_id, response=response)
                except Exception as interactive_error:
                    logger.error(f"Error sending interactive message: {str(interactive_error)}")
                    send_whatsapp_message(recipient_id=recipient_id, message_text=response.get('text', ''))
        else:
            # No options, just send as a simple text message
            send_whatsapp_message(recipient_id=recipient_id, message_text=response.get('text', ''))
            
    except Exception as e:
        logger.error(f"Error sending WhatsApp response: {str(e)}")
        try:
            # Send a simple fallback message
            fallback_message = "Sorry, there was an error. Please try again.\n\nעצטער, היתה שגיאה. אנא נסה שוב.\n\nعذراً، حدث خطأ. يرجى المحاولة مرة أخرى."
            send_whatsapp_message(recipient_id=recipient_id, message_text=fallback_message)
        except Exception as fallback_error:
            logger.error(f"Error sending fallback message: {str(fallback_error)}")

def handle_interactive_message(message, sender_id):
    """Process interactive message like button clicks"""
    try:
        # Extract the button ID and title that was clicked
        button_response = None
        if 'interactive' in message and 'button_reply' in message['interactive']:
            button_response = message['interactive']['button_reply']
            button_id = button_response.get('id', '')
            button_title = button_response.get('title', '')
            
            logger.info(f"User {sender_id} clicked button: {button_title} (ID: {button_id})")
            
            # Check if this is an Arabic button
            if any(is_arabic(char) for char in button_title):
                # For Arabic, use the button title as the text input
                logger.info(f"Processing Arabic button selection: {button_title}")
                dialogflow_response = process_arabic_text(button_title, sender_id)
                return dialogflow_response
            else:
                # For Hebrew, pass the button title to the flow manager
                logger.info(f"Processing Hebrew button selection: {button_title}")
                return process_hebrew_flow(button_title, sender_id)
    except Exception as e:
        logger.error(f"Error handling interactive message: {str(e)}", exc_info=True)
        
    # Default fallback
    return {
        "text": "Sorry, I couldn't process your selection. Please try again.",
        "options": ["Start Over"]
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(debug=True, host='0.0.0.0', port=port)
