import logging
import os
from google.cloud.dialogflowcx_v3beta1 import SessionsClient
from google.cloud.dialogflowcx_v3beta1.types import TextInput, QueryInput, QueryParameters, EventInput
from google.oauth2 import service_account
import re

logger = logging.getLogger(__name__)

def get_session_client():
    """
    Initialize and return a Dialogflow CX session client
    
    Returns:
        SessionsClient: Initialized Dialogflow CX client
    """
    try:
        # Check if client is already initialized as a global variable
        global dialogflow_client
        if 'dialogflow_client' in globals() and dialogflow_client:
            return dialogflow_client
            
        # Load service account credentials
        SERVICE_ACCOUNT_FILE = 'service_account.json'
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(f"Service account file '{SERVICE_ACCOUNT_FILE}' not found")
        
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        logger.debug("Successfully loaded service account credentials")

        # Configure client options with regional endpoint
        from google.api_core import client_options
        client_options_obj = client_options.ClientOptions(
            api_endpoint=f"{os.getenv('DIALOGFLOW_LOCATION', 'us-central1')}-dialogflow.googleapis.com"
        )
        
        # Initialize Dialogflow CX client with credentials and regional endpoint
        dialogflow_client = SessionsClient(
            credentials=credentials,
            client_options=client_options_obj
        )
        
        return dialogflow_client
        
    except Exception as e:
        logger.error(f"Failed to initialize Dialogflow client: {str(e)}")
        raise

def detect_intent_texts(text, session_id, language_code='ar'):
    """
    Detect the intent of a text using Dialogflow
    
    Args:
        text: The text to analyze
        session_id: The session ID to use
        language_code: The language code to use
        
    Returns:
        dict: Dictionary with detected intent and entities
    """
    try:
        # Get the session client
        session_client = get_session_client()
        
        # Get the session path
        project_id = os.getenv('DIALOGFLOW_PROJECT_ID', 'dr-wasem')
        location = os.getenv('DIALOGFLOW_LOCATION', 'us-central1')
        agent_id = os.getenv('DIALOGFLOW_AGENT_ID', 'e5015670-9395-4578-993b-98a1b0aee1f0')
        session_path = f"projects/{project_id}/locations/{location}/agents/{agent_id}/sessions/{session_id}"
        
        logger.debug(f"Sending text to Dialogflow: '{session_id}...' with language: {language_code}")
        
        # Set the text input
        text_input = TextInput(text=text)
        query_input = QueryInput(text=text_input, language_code=language_code)
        query_params = QueryParameters(time_zone="Asia/Jerusalem")
        
        # Send the request
        response = session_client.detect_intent(
            request={"session": session_path, "query_input": query_input, "query_params": query_params}
        )
        
        # Extract the response
        return extract_arabic_response(response)
        
    except Exception as e:
        logger.error(f"Error in detect_intent_texts: {e}", exc_info=True)
        return {
            "text": "عذراً، هناك مشكلة فنية. الرجاء المحاولة مرة أخرى.",
            "options": ["حجز موعد", "معلومات"]
        }

def extract_arabic_response(response):
    """
    Extract the response text and options from the Dialogflow response for Arabic
    
    Args:
        response: Dialogflow response object
        
    Returns:
        dict: Dictionary with text and options
    """
    try:
        # Initialize with empty text and default options
        text = ""
        options = ['الخدمات', 'حجز موعد', 'دعم ما بعد العلاج']
        
        # Safely extract text from response messages
        if hasattr(response, 'query_result') and hasattr(response.query_result, 'response_messages'):
            messages = response.query_result.response_messages
            
            # Extract text from any text messages
            for message in messages:
                if hasattr(message, 'text') and hasattr(message.text, 'text') and len(message.text.text) > 0:
                    message_text = message.text.text[0]
                    # Clean up text - remove quotes
                    message_text = message_text.replace('"', '').replace("'", '')
                    text += message_text + " "
                
                # Try to extract options from payload
                if hasattr(message, 'payload') and message.payload:
                    try:
                        # Log payload type for debugging
                        logger.debug(f"Message has payload of type: {type(message.payload)}")
                        
                        # Extract from richContent if present
                        if hasattr(message.payload, 'fields') and 'richContent' in message.payload.fields:
                            rich_content = message.payload.fields['richContent'].list_value.values
                            
                            # Process each item in the first array of richContent
                            if rich_content and len(rich_content) > 0 and hasattr(rich_content[0], 'list_value'):
                                for item in rich_content[0].list_value.values:
                                    if hasattr(item, 'struct_value') and hasattr(item.struct_value, 'fields'):
                                        # Extract options if present
                                        if 'options' in item.struct_value.fields:
                                            options = []  # Reset options when we find them in the payload
                                            for opt in item.struct_value.fields['options'].list_value.values:
                                                if 'text' in opt.struct_value.fields:
                                                    opt_text = opt.struct_value.fields['text'].string_value
                                                    options.append(opt_text)
                    except Exception as e:
                        logger.error(f"Error extracting options from payload: {e}", exc_info=True)
        
        # Clean and trim text
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        
        # If we didn't extract any text, use a default message
        if not text:
            text = "مرحباً بك في عيادة د. وسيم، كيف يمكنني مساعدتك اليوم؟"
            
        logger.debug(f"Extracted Arabic response: {{'text': '{text}', 'options': {options}}}")
        
        return {
            "text": text,
            "options": options
        }
    except Exception as e:
        logger.error(f"Error in extract_arabic_response: {e}", exc_info=True)
        return {
            "text": "مرحباً، أنا المساعد الطبي لعيادة د. وسيم. كيف يمكنني مساعدتك اليوم؟",
            "options": ['الخدمات', 'حجز موعد', 'معلومات العيادة']
        }

def trigger_dialogflow_event(session_id, event_name, language_code='ar', parameters=None):
    """
    Trigger a specific event in Dialogflow
    
    Args:
        session_id: The session ID to use
        event_name: The event to trigger
        language_code: The language code to use
        parameters: Optional parameters to send with the event
        
    Returns:
        dict: Dictionary with response text and options
    """
    try:
        # Get the session client
        session_client = get_session_client()
        
        # Get the session path
        project_id = os.getenv('DIALOGFLOW_PROJECT_ID', 'dr-wasem')
        location = os.getenv('DIALOGFLOW_LOCATION', 'us-central1')
        agent_id = os.getenv('DIALOGFLOW_AGENT_ID', 'e5015670-9395-4578-993b-98a1b0aee1f0')
        session_path = f"projects/{project_id}/locations/{location}/agents/{agent_id}/sessions/{session_id}"
        
        logger.debug(f"Triggering Dialogflow event: '{event_name}' for session: {session_id}")
        
        # Create event input
        event_input = EventInput(event=event_name)
        if parameters:
            event_input.parameters = parameters
            
        query_input = QueryInput(event=event_input, language_code=language_code)
        
        # Send the request
        response = session_client.detect_intent(
            request={"session": session_path, "query_input": query_input}
        )
        
        # Extract the response
        return extract_arabic_response(response)
        
    except Exception as e:
        logger.error(f"Error triggering Dialogflow event: {e}", exc_info=True)
        return {
            "text": "عذراً، هناك مشكلة فنية. الرجاء المحاولة مرة أخرى.",
            "options": ["الخدمات", "حجز موعد", "معلومات"]
        }
