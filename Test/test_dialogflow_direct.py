import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google.cloud.dialogflowcx_v3beta1 import SessionsClient
from google.cloud.dialogflowcx_v3beta1.types import TextInput, QueryInput, QueryParameters
from google.oauth2 import service_account
from google.api_core import client_options
import json

load_dotenv()

def test_dialogflow_direct():
    """Send messages directly to Dialogflow CX API to diagnose issues"""
    print("=== DIRECT DIALOGFLOW CX API TEST ===\n")
    
    # Setup Google Cloud credentials
    SERVICE_ACCOUNT_FILE = 'service_account.json'
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    
    # Configure client options with regional endpoint
    client_options_obj = client_options.ClientOptions(
        api_endpoint=f"{os.getenv('DIALOGFLOW_LOCATION')}-dialogflow.googleapis.com"
    )
    
    # Initialize Dialogflow CX client with credentials
    dialogflow_client = SessionsClient(
        credentials=credentials,
        client_options=client_options_obj
    )
    
    # Build agent path
    agent_path = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}/locations/{os.getenv('DIALOGFLOW_LOCATION')}/agents/{os.getenv('DIALOGFLOW_AGENT_ID')}"
    print(f"Agent path: {agent_path}")
    
    # Test both Hebrew and Arabic messages
    test_messages = [
        {"text": "שלום", "language": "he", "description": "Hebrew greeting"},
        {"text": "مرحبا", "language": "ar", "description": "Arabic greeting"}
    ]
    
    for test in test_messages:
        print(f"\n== Testing: {test['description']} ==")
        print(f"Message: {test['text']}")
        print(f"Language: {test['language']}")
        
        # Create session
        session_id = f"test_{test['language']}"
        session = f"{agent_path}/sessions/{session_id}"
        
        # Create text input
        text_input = TextInput(text=test['text'])
        query_input = QueryInput(
            text=text_input,
            language_code=test['language']
        )
        
        # Create parameters
        parameters = QueryParameters(time_zone="Asia/Jerusalem")
        
        # Create request
        request = {
            "session": session,
            "query_input": query_input,
            "query_params": parameters
        }
        
        # Send request to Dialogflow
        print("\nSending request to Dialogflow...")
        response = dialogflow_client.detect_intent(request=request)
        
        # Print response details for debugging
        print(f"Response intent: {response.query_result.intent.display_name}")
        print(f"Response language: {response.query_result.language_code}")
        print(f"Response confidence: {response.query_result.intent_detection_confidence}")
        
        # Print response messages
        print("\nResponse messages:")
        for msg in response.query_result.response_messages:
            if hasattr(msg, 'text') and msg.text.text:
                for text in msg.text.text:
                    print(f"- {text}")
            elif hasattr(msg, 'payload'):
                print(f"- Payload: {dict(msg.payload)}")
        
        # Check if the response language matches the requested language
        if response.query_result.language_code != test['language']:
            print(f"\n⚠️ WARNING: Requested language '{test['language']}' but got '{response.query_result.language_code}'")
        
        # Additional info
        print("\nFull response parameters:")
        print(f"- Session parameters: {dict(response.query_result.parameters)}")
        print(f"- Current page: {response.query_result.current_page.display_name}")

if __name__ == "__main__":
    test_dialogflow_direct()
