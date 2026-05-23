import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_nlp.hebrew_nlu import understand_hebrew_text
from custom_nlp.hebrew_nlp import detect_hebrew_intent

def test_hebrew_nlu():
    """Test the enhanced Hebrew NLU module with various inputs"""
    test_cases = [
        # Test for services intent with different phrasings
        {"text": "אילו שירותים אתם מספקים?", "expected_intent": "services"},
        {"text": "מה אתם מציעים במרפאה?", "expected_intent": "services"},
        {"text": "איזה טיפולים יש לכם?", "expected_intent": "services"},
        {"text": "מה אפשר לעשות אצלכם?", "expected_intent": "services"},
        
        # Test for appointment requests
        {"text": "אני רוצה לקבוע תור", "expected_intent": "appointment_request"},
        {"text": "מתי אפשר להגיע?", "expected_intent": "appointment_request"},
        {"text": "יש תורים פנויים?", "expected_intent": "appointment_request"},
        
        # Test for price inquiries
        {"text": "כמה עולה טיפול?", "expected_intent": "prices"},
        {"text": "מה המחירים?", "expected_intent": "prices"},
        {"text": "תעריף להזרקה?", "expected_intent": "prices"},
        
        # Test for doctor info
        {"text": "מי הרופא?", "expected_intent": "doctor_info"},
        {"text": "ספר לי על דוקטור וסים", "expected_intent": "doctor_info"},
        
        # Test for location
        {"text": "איפה אתם נמצאים?", "expected_intent": "location"},
        {"text": "כתובת של המרפאה?", "expected_intent": "location"},
        
        # Test for greetings
        {"text": "שלום", "expected_intent": "greeting"},
        {"text": "היי, מה נשמע?", "expected_intent": "greeting"},
        
        # Test for complex or mixed queries
        {"text": "אני רוצה לדעת על טיפולים וגם לקבוע תור", "expected_intent": "services"},
        {"text": "שלום, אפשר לדעת כמה עולה הזרקה?", "expected_intent": "prices"}
    ]
    
    print("=== HEBREW NLU TEST ===\n")
    
    # Test with new NLU module directly
    print("TESTING DIRECT NLU UNDERSTANDING:")
    print("---------------------------------\n")
    
    for i, case in enumerate(test_cases[:10]):  # Use first 10 cases
        text = case["text"]
        expected = case["expected_intent"]
        
        result = understand_hebrew_text(text)
        intent = result["intent"]
        confidence = result["confidence"]
        entities = result["entities"]
        
        status = "✅" if intent == expected else "❌"
        print(f"{i+1}. {status} Input: '{text}'")
        print(f"   Expected: '{expected}', Got: '{intent}' (Confidence: {confidence:.2f})")
        
        if entities:
            print(f"   Entities: {entities}")
        print("")
    
    # Test with enhanced detect_hebrew_intent function
    print("\nTESTING ENHANCED DETECT_HEBREW_INTENT:")
    print("-------------------------------------\n")
    
    for i, case in enumerate(test_cases):
        text = case["text"]
        expected = case["expected_intent"]
        
        result = detect_hebrew_intent(text)
        intent = result["intent"]
        confidence = result["confidence"]
        
        status = "✅" if intent == expected else "❌"
        print(f"{i+1}. {status} Input: '{text}'")
        print(f"   Expected: '{expected}', Got: '{intent}' (Confidence: {confidence:.2f})")
        print("")
    
    # Test specific service inquiries
    print("\nTESTING SPECIFIC SERVICE INQUIRIES:")
    print("----------------------------------\n")
    
    service_inquiries = [
        "האם אתם עושים הזרקות?",
        "יש לכם טיפול בכאבי גב?",
        "אתם מטפלים בכאבי ברכיים?",
        "יש לכם מומחה לפריצת דיסק?",
        "האם ד״ר וסים עושה טיפול בכתף?"
    ]
    
    for text in service_inquiries:
        result = detect_hebrew_intent(text)
        
        print(f"Input: '{text}'")
        print(f"Intent: '{result['intent']}' (Confidence: {result['confidence']:.2f})")
        print(f"Entities: {result['entities']}")
        print("")

if __name__ == "__main__":
    test_hebrew_nlu()
