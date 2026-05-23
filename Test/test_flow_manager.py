import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_nlp.flow_manager import (
    process_hebrew_flow, 
    start_specific_flow,
    personalize_message
)
import json

def test_flow_manager():
    """Test the flow manager's ability to handle Hebrew conversations"""
    print("=== FLOW MANAGER TEST ===\n")
    
    # Test basic flow processing
    print("1. Testing basic greeting:")
    response = process_hebrew_flow("שלום")
    print(f"Input: 'שלום'")
    print(f"Response: '{response['text']}'")
    print(f"Options: {response['options']}")
    print(f"Flow: {response.get('flow', 'N/A')}, State: {response.get('state', 'N/A')}")
    print(f"Intent: {response.get('detected_intent', 'N/A')}")
    print()
    
    # Test appointment flow
    print("2. Testing appointment flow initiation:")
    response = process_hebrew_flow("אני רוצה לקבוע תור")
    print(f"Input: 'אני רוצה לקבוע תור'")
    print(f"Response: '{response['text']}'")
    print(f"Options: {response['options']}")
    print(f"Flow: {response.get('flow', 'N/A')}, State: {response.get('state', 'N/A')}")
    print()

    # Test services catalog
    print("3. Testing services catalog:")
    response = process_hebrew_flow("מה הטיפולים שאתם מציעים?")
    print(f"Input: 'מה הטיפולים שאתם מציעים?'")
    print(f"Response: '{response['text'][:100]}...'")
    print(f"Options: {response['options']}")
    print(f"Flow: {response.get('flow', 'N/A')}, State: {response.get('state', 'N/A')}")
    print()
    
    # Test emergency override
    print("4. Testing emergency detection:")
    response = process_hebrew_flow("יש לי חום גבוה מאוד אחרי ההזרקה")
    print(f"Input: 'יש לי חום גבוה מאוד אחרי ההזרקה'")
    print(f"Response: '{response['text']}'")
    print(f"Options: {response['options']}")
    print(f"Priority: {response.get('priority', 'normal')}")
    print()
    
    # Test starting specific flow
    print("5. Testing starting specific flow (injections):")
    response = start_specific_flow("catalog", "injections", "test_phone")
    print(f"Response: '{response['text']}'")
    print(f"Options: {response['options']}")
    print(f"Flow: {response.get('flow', 'N/A')}, State: {response.get('state', 'N/A')}")
    print()
    
    # Test message personalization
    print("6. Testing message personalization:")
    template = "שלום {name}, התור שלך נקבע ליום {day} בשעה {time}."
    context = {
        "name": "משה",
        "day": "רביעי",
        "time": "16:30"
    }
    personalized = personalize_message(template, context)
    print(f"Template: '{template}'")
    print(f"Context: {context}")
    print(f"Result: '{personalized}'")

if __name__ == "__main__":
    test_flow_manager()
