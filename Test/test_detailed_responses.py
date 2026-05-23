import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_nlp.flow_manager import process_hebrew_flow
from custom_nlp.fallback_handler import handle_unclear_input
from custom_nlp.response_generator import generate_expanded_information

def test_detailed_responses():
    """Test the system's ability to provide detailed information and handle unfamiliar inputs"""
    print("=== DETAILED RESPONSES AND FALLBACK HANDLING TEST ===\n")
    
    # Test detailed treatment information
    print("1. Testing detailed treatment information:")
    topics = ["הזרקת סטרואידים", "חומצה היאלורונית", "טיפול PRP", "אולטרסאונד לתינוקות"]
    
    for topic in topics:
        detailed_info = generate_expanded_information(topic)
        print(f"\n---- Detailed information for {topic} ----")
        # Print first 100 characters as a preview
        print(f"{detailed_info[:150]}...\n")
        print(f"Total length: {len(detailed_info)} characters")
    
    # Test unfamiliar input handling
    print("\n2. Testing unfamiliar input handling:")
    unfamiliar_inputs = [
        "כואב לי בצד ימין",
        "עוד כמה זמן ירד הנפיחות?",
        "איך אני יודע אם הטיפול מצליח?",
        "אני לא בטוח מה לעשות",
        "משהו לא ברור"
    ]
    
    for text in unfamiliar_inputs:
        response = handle_unclear_input(text, 0.25)
        print(f"\nInput: '{text}'")
        print(f"Response: '{response['text']}'")
        print(f"Options: {response['options']}")
    
    # Test mid-conversation option reduction
    print("\n3. Testing mid-conversation option reduction:")
    
    # Simulate a multi-turn conversation
    print("\nSimulating conversation with multiple turns:")
    phone = "test_phone_123"
    
    # Turn 1
    response = process_hebrew_flow("שלום", phone)
    print(f"Turn 1 - Options count: {len(response.get('options', []))}")
    print(f"Options: {response.get('options', [])}")
    
    # Turn 2
    response = process_hebrew_flow("אני רוצה מידע על הזרקות", phone)
    print(f"Turn 2 - Options count: {len(response.get('options', []))}")
    print(f"Options: {response.get('options', [])}")
    
    # Turn 3
    response = process_hebrew_flow("הזרקת סטרואידים", phone)
    print(f"Turn 3 - Options count: {len(response.get('options', []))}")
    print(f"Options: {response.get('options', [])}")
    
    # Turn 4
    response = process_hebrew_flow("אני רוצה מידע נוסף", phone)
    print(f"Turn 4 - Options count: {len(response.get('options', []))}")
    print(f"Options: {response.get('options', [])}")
    
    # Turn 5
    response = process_hebrew_flow("תודה", phone)
    print(f"Turn 5 - Options count: {len(response.get('options', []))}")
    print(f"Options: {response.get('options', [])}")

if __name__ == "__main__":
    test_detailed_responses()
