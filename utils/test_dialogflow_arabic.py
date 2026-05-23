"""
A utility script to test the Dialogflow integration for Arabic messages
Run this directly to test Arabic queries and see the responses
"""
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Load environment variables
load_dotenv()

def test_arabic_query(text, session_id="test_session"):
    """
    Test an Arabic query and print the response in a readable format
    
    Args:
        text (str): Arabic text to send to Dialogflow
        session_id (str): Test session ID
        
    Returns:
        dict: The response from Dialogflow
    """
    try:
        from utils.dialogflow_client import detect_intent_texts
        
        print(f"\n==== Testing Arabic Query ====")
        print(f"Query: {text}")
        print("\nSending to Dialogflow...\n")
        
        response = detect_intent_texts(session_id, text, 'ar')
        
        print("==== Response ====")
        print(f"Intent: {response.get('detected_intent', 'unknown')}")
        print(f"Confidence: {response.get('confidence', 0)}")
        print(f"Text: {response.get('text', '')}")
        
        if 'options' in response and response['options']:
            print("\nOptions:")
            for i, option in enumerate(response['options'], 1):
                print(f"  {i}. {option}")
        
        return response
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.exception("Error in test_arabic_query")
        return None

def run_test_suite():
    """Run a series of predefined Arabic queries"""
    test_queries = [
        "السلام عليكم",
        "أريد حجز موعد",
        "ما هي خدماتكم؟",
        "من هو الدكتور وسيم؟",
        "هل تقدمون حقن المفاصل؟"
    ]
    
    for query in test_queries:
        test_arabic_query(query)
        print("\n" + "-" * 50 + "\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with specific query from command line argument
        test_arabic_query(sys.argv[1])
    else:
        print("Arabic Dialogflow Tester")
        print("=======================")
        print("1. Run test suite")
        print("2. Enter custom query")
        choice = input("Enter choice (1/2): ")
        
        if choice == "1":
            run_test_suite()
        elif choice == "2":
            query = input("Enter Arabic text: ")
            test_arabic_query(query)
        else:
            print("Invalid choice")
