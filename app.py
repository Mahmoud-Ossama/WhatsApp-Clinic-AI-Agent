from flask import Flask, request
from twilio.rest import Client
from google.cloud.dialogflowcx_v3beta1 import SessionsClient
from google.cloud.dialogflowcx_v3beta1.types import TextInput, QueryInput
from google.oauth2 import service_account
import os
import logging
from dotenv import load_dotenv
from google.api_core import client_options

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

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

app = Flask(__name__)

# Initialize Twilio client
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

@app.route('/')
def home():
    return 'WhatsApp-Dialogflow Webhook is running!'

@app.route('/webhook', methods=['GET'])
def verify():
    """Handle webhook verification"""
    return 'Webhook is ready!', 200

def extract_response_text(response):
    """Extract text from Dialogflow response, handling both text and custom payload formats"""
    try:
        if not response.query_result.response_messages:
            return "No response available."

        messages = []
        for msg in response.query_result.response_messages:
            if msg.text.text:
                # Handle regular text responses
                messages.extend(msg.text.text)
            elif msg.payload:
                # Handle custom payload
                rich_content = msg.payload.fields.get('richContent')
                if rich_content and rich_content.list_value.values:
                    for content in rich_content.list_value.values:
                        for item in content.list_value.values:
                            # Handle description type
                            if item.struct_value.fields.get('type').string_value == 'description':
                                title = item.struct_value.fields.get('title').string_value
                                text_list = item.struct_value.fields.get('text').list_value.values
                                messages.append(f"{title}")
                                messages.extend([t.string_value for t in text_list])
                            
                            # Handle chips/options type
                            if item.struct_value.fields.get('type').string_value == 'chips':
                                options = item.struct_value.fields.get('options').list_value.values
                                option_texts = [opt.struct_value.fields.get('text').string_value 
                                             for opt in options]
                                messages.append("\n".join(option_texts))

        return "\n\n".join(messages) if messages else "I apologize, but I couldn't generate a proper response."
    except Exception as e:
        logger.error(f"Error extracting response text: {e}")
        return "Sorry, I'm having trouble processing the response."

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        logger.debug(f"Received webhook request: {request.values}")
        if not request.values:
            logger.error("No request values received")
            return 'No data received', 400

        # Get incoming message from WhatsApp
        incoming_msg = request.values.get('Body', '').strip()
        sender_phone = request.values.get('From', '')

        # Create session
        session_id = sender_phone.replace('whatsapp:', '')
        session = f"{agent_path}/sessions/{session_id}"

        # Create the request message
        text_input = TextInput(text=incoming_msg)
        query_input = QueryInput(text=text_input, language_code="en")
        
        # Updated detect_intent call with correct parameter format
        request_message = {
            "session": session,
            "query_input": query_input
        }
        
        response = dialogflow_client.detect_intent(request=request_message)
        logger.debug(f"Raw Dialogflow response: {response}")
        
        # Extract formatted response text
        fulfillment_text = extract_response_text(response)
        logger.debug(f"Formatted response text: {fulfillment_text}")

        # Send response back to WhatsApp
        twilio_client.messages.create(
            body=fulfillment_text,
            from_='whatsapp:+14155238886',
            to=sender_phone
        )

        logger.debug(f"Sent WhatsApp response to {sender_phone}")
        return '', 200

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

if __name__ == '__main__':
    logger.info(f"Server starting on port 5000...")
    app.run(debug=True, port=5000, host='0.0.0.0')
