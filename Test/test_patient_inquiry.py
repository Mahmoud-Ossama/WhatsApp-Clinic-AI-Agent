import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_nlp.flow_manager import (
    process_hebrew_flow, 
    process_patient_complaint,
    start_specific_flow
)

def test_patient_inquiry_flow():
    """Test the new patient inquiry flow for handling complaints"""
    print("=== PATIENT INQUIRY FLOW TEST ===\n")
    
    # Test basic complaint detection
    complaints = [
        "יש לי כאב חזק בגב כבר שבועיים",
        "הברך שלי כואבת אחרי נפילה",
        "סובל מכאבים בצוואר",
        "אני חושב שיש לי פריצת דיסק",
        "נפלתי ויש לי כאבים ביד"
    ]
    
    for complaint in complaints:
        print(f"Testing complaint: '{complaint}'")
        response = process_hebrew_flow(complaint, "test_phone")
        print(f"Response: '{response['text']}'")
        print(f"Options: {response['options']}")
        print(f"Detected intent: {response.get('detected_intent', 'N/A')}")
        print(f"Flow: {response.get('flow', 'N/A')}, State: {response.get('state', 'N/A')}")
        print()
    
    # Test full conversation flow
    print("\nTesting complete patient inquiry conversation flow:")
    
    # Step 1: Initial complaint
    response = process_hebrew_flow("יש לי כאב בברך כבר חודש", "test_phone_2")
    print(f"User: 'יש לי כאב בברך כבר חודש'")
    print(f"Bot: '{response['text']}'")
    print(f"Options: {response['options']}")
    print()
    
    # Step 2: Select complaint type
    response = process_hebrew_flow("כאבי ברכיים/מפרקים", "test_phone_2")
    print(f"User: 'כאבי ברכיים/מפרקים'")
    print(f"Bot: '{response['text']}'")
    print(f"Options: {response['options']}")
    print()
    
    # Step 3: Select duration
    response = process_hebrew_flow("מעל חודש", "test_phone_2")
    print(f"User: 'מעל חודש'")
    print(f"Bot: '{response['text']}'")
    print(f"Options: {response['options']}")
    print()
    
    # Step 4: Prior treatment
    response = process_hebrew_flow("כדורים לכאבים", "test_phone_2")
    print(f"User: 'כדורים לכאבים'")
    print(f"Bot: '{response['text']}'")
    print(f"Options: {response['options']}")
    print()
    
    # Step 5: Ask about cost
    response = process_hebrew_flow("מה עלות הטיפול?", "test_phone_2")
    print(f"User: 'מה עלות הטיפול?'")
    print(f"Bot: '{response['text']}'")
    print(f"Options: {response['options']}")
    print()

if __name__ == "__main__":
    test_patient_inquiry_flow()
