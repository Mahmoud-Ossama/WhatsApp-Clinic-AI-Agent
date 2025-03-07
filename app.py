import atexit
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
from dashboard.views import AdminModelView, PatientView,  FollowUpView, DashboardView as AdminDashboardView  # Updated import
from utils.scheduler import init_scheduler
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.DEBUG)
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

# Add only Patient and FollowUp views
admin.add_view(PatientView(db.patients, 'المرضى', endpoint='patient_admin'))
admin.add_view(FollowUpView(db.followups, 'المتابعات', endpoint='followup_admin'))

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

def send_whatsapp_message(to_number, message_text, options=None):
    """Send message using WhatsApp Cloud API with button support"""
    try:
        to_number = to_number.replace('whatsapp:', '').strip()
        
        if options and len(options) > 0:
            # Split message_text into sentences
            sentences = message_text.split('.')
            header = sentences[0].strip()
            body = '.'.join(sentences[1:]).strip()
            
            if len(options) > 3:
                # If more than 3 options, add them to the body text
                body += "\n\nالخيارات الإضافية:\n" + "\n".join(options[3:])
            
            payload = create_whatsapp_button_message(
                to_number=to_number,
                header_text=header,
                body_text=body,
                options=options
            )
        else:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_number,
                "type": "text",
                "text": {"body": message_text}
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

@app.route('/')
def home():
    return 'WhatsApp-Dialogflow Webhook is running!'

@app.route('/webhook', methods=['GET'])
def verify():
    """Handle webhook verification from WhatsApp Cloud API"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == os.getenv('WHATSAPP_WEBHOOK_TOKEN'):
            logger.info("Webhook verified")
            return challenge
        return 'Invalid verification token', 403

    return 'Invalid verification request', 400

def extract_response_text(response):
    """Enhanced response text extraction with options list"""
    try:
        if not response.query_result.response_messages:
            return "No response available.", None

        messages = []
        options = []
        
        for msg in response.query_result.response_messages:
            try:
                if hasattr(msg, 'text') and msg.text.text:
                    messages.extend(msg.text.text)
                elif hasattr(msg, 'payload'):
                    payload_dict = dict(msg.payload)
                    rich_content = payload_dict.get('richContent', [])
                    
                    if rich_content and len(rich_content) > 0:
                        for content in rich_content[0]:
                            if content.get('type') == 'description':
                                title = content.get('title', '')
                                text_list = content.get('text', [])
                                if title:
                                    messages.append(title)
                                messages.extend(text_list)
                            
                            elif content.get('type') == 'chips':
                                options.extend([
                                    opt.get('text', '') 
                                    for opt in content.get('options', [])
                                ])
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                continue

        message_text = "\n\n".join(filter(None, messages))
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
        data = request.json
        logger.debug(f"Received webhook data: {data}")

        if 'entry' not in data:
            return 'No entry in webhook data', 400

        try:
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']

            # Handle status updates
            if 'statuses' in value:
                status = value['statuses'][0]
                logger.info(f"Message Status Update - ID: {status.get('id')}, "
                          f"Status: {status.get('status')}, "
                          f"Timestamp: {status.get('timestamp')}")
                return '', 200

            # Handle messages
            if 'messages' in value:
                message = value['messages'][0]
                
                if message['type'] == 'interactive':
                    # Handle button response
                    if 'button_reply' in message:
                        incoming_msg = message['button_reply']['title']
                    else:
                        incoming_msg = message.get('interactive', {}).get('button_reply', {}).get('title', '')
                elif message['type'] == 'text':
                    incoming_msg = message['text']['body']
                else:
                    logger.info(f"Received non-handled message type: {message['type']}")
                    return '', 200

                sender_phone = message['from']
                
                # Store message timestamp
                db.message_history.insert_one({
                    'phone': sender_phone,
                    'timestamp': datetime.utcnow(),
                    'message': incoming_msg
                })

                # Check if session should be reset
                if should_reset_session(sender_phone):
                    # Create event to reset session
                    event_input = EventInput(event='sys.reset')
                    query_input = QueryInput(event=event_input)
                    request_message = {
                        "session": f"{agent_path}/sessions/{sender_phone}",
                        "query_input": query_input
                    }
                    dialogflow_client.detect_intent(request=request_message)
                    logger.info(f"Reset session for {sender_phone}")

                # Create session and process with Dialogflow
                session_id = sender_phone
                session = f"{agent_path}/sessions/{session_id}"

                # Detect language and create query input
                detected_lang = "ar" if any('\u0600' <= c <= '\u06FF' for c in incoming_msg) else "en"
                text_input = TextInput(text=incoming_msg)
                query_input = QueryInput(
                    text=text_input,
                    language_code=detected_lang
                )
                
                parameters = QueryParameters(time_zone="Asia/Jerusalem")
                request_message = {
                    "session": session,
                    "query_input": query_input,
                    "query_params": parameters
                }
                
                # Get and process Dialogflow response
                response = dialogflow_client.detect_intent(request=request_message)
                logger.debug(f"Raw Dialogflow response: {response}")
                
                # Extract text and options
                fulfillment_text, options = extract_response_text(response)
                logger.debug(f"Formatted response text: {fulfillment_text}")
                logger.debug(f"Options: {options}")

                # Send response with options if available
                send_whatsapp_message(sender_phone, fulfillment_text, options)
                return '', 200

            return '', 200

        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing webhook data: {str(e)}")
            logger.debug(f"Problematic data structure: {data}")
            return '', 200  # Return 200 for unhandled message types

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return f"Error: {str(e)}", 500

# Add error handlers
@app.errorhandler(404)
def not_found(e):
    return 'The requested URL was not found.', 404

@app.errorhandler(500)
def server_error(e):
    return 'Internal server error.', 500

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

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(debug=True, host='0.0.0.0', port=port)
