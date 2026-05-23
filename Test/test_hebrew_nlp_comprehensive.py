import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_nlp.hebrew_nlp import detect_hebrew_intent, process_hebrew_message
import json

def test_hebrew_nlp_comprehensive():
    """Test the comprehensive Hebrew NLP with various inputs"""
    test_cases = [
        # Greetings
        {"text": "שלום", "expected_intent": "greeting"},
        {"text": "היי, מה נשמע", "expected_intent": "greeting"},
        {"text": "ערב טוב", "expected_intent": "greeting"},
        
        # Appointment requests
        {"text": "אני רוצה לקבוע תור", "expected_intent": "appointment_request"},
        {"text": "מתי אפשר להגיע לפגישה", "expected_intent": "appointment_request"},
        {"text": "אני צריך מועד לטיפול", "expected_intent": "appointment_request"},
        
        # Appointment changes
        {"text": "אני רוצה לשנות את התור שלי", "expected_intent": "appointment_reschedule"},
        {"text": "אפשר לדחות את הפגישה", "expected_intent": "appointment_reschedule"},
        
        # Service inquiries
        {"text": "אילו טיפולים אתם מציעים", "expected_intent": "services"},
        {"text": "מה הטיפולים האפשריים", "expected_intent": "services"},
        {"text": "אתם עושים טיפול בכאבי גב", "expected_intent": "services"},
        
        # Price inquiries
        {"text": "כמה עולה טיפול", "expected_intent": "prices"},
        {"text": "מה המחיר של הזרקה", "expected_intent": "prices"},
        {"text": "אפשר לדעת על תעריפים", "expected_intent": "prices"},
        
        # Location questions
        {"text": "איפה אתם נמצאים", "expected_intent": "location"},
        {"text": "מה הכתובת של המרפאה", "expected_intent": "location"},
        {"text": "איך מגיעים אליכם", "expected_intent": "location"},
        
        # Hours inquiries
        {"text": "מתי אתם פתוחים", "expected_intent": "hours"},
        {"text": "שעות פעילות", "expected_intent": "hours"},
        {"text": "באילו ימים יש קבלה", "expected_intent": "hours"},
        
        # Doctor information
        {"text": "מי הרופא", "expected_intent": "doctor_info"},
        {"text": "מה ההתמחות של דוקטור וסים", "expected_intent": "doctor_info"},
        {"text": "כמה שנות ניסיון יש לד\"ר", "expected_intent": "doctor_info"},
        
        # Insurance questions
        {"text": "אתם עובדים עם קופת חולים", "expected_intent": "insurance"},
        {"text": "יש החזר מביטוח", "expected_intent": "insurance"},
        {"text": "מקבלים מכבי", "expected_intent": "insurance"},
        
        # Thank you messages
        {"text": "תודה רבה", "expected_intent": "thank_you"},
        {"text": "אני מודה לך", "expected_intent": "thank_you"},
        
        # Confirmations
        {"text": "כן, מאשר", "expected_intent": "confirm"},
        {"text": "מסכים", "expected_intent": "confirm"},
        {"text": "נשמע טוב", "expected_intent": "confirm"},
        
        # Declines
        {"text": "לא תודה", "expected_intent": "decline"},
        {"text": "לא מעוניין", "expected_intent": "decline"},
        
        # Help requests
        {"text": "תוכל לעזור לי", "expected_intent": "help"},
        {"text": "אני צריך עזרה", "expected_intent": "help"},
        
        # Emergency
        {"text": "זה דחוף", "expected_intent": "emergency"},
        {"text": "יש לי כאב חזק", "expected_intent": "emergency"},
        
        # Goodbyes
        {"text": "להתראות", "expected_intent": "goodbye"},
        {"text": "ביי", "expected_intent": "goodbye"},
        
        # Complex inputs with multiple intents
        {"text": "שלום, אני רוצה לקבוע תור לטיפול בכאבי גב", "expected_intent": "appointment_request"},
        {"text": "יש לי כאבים בצוואר וראיתי שיש לכם טיפול לזה, כמה זה עולה?", "expected_intent": "prices"},
        {"text": "אני רוצה לדעת אם אתם פתוחים ביום חמישי ואם אפשר לקבוע תור", "expected_intent": "appointment_request"},
    ]
    
    print("=== COMPREHENSIVE HEBREW NLP TEST ===\n")
    
    # Test intent detection
    print("TESTING INTENT DETECTION:")
    print("--------------------------\n")
    
    for i, case in enumerate(test_cases):
        text = case["text"]
        expected = case["expected_intent"]
        
        result = detect_hebrew_intent(text)
        detected = result["intent"]
        confidence = result["confidence"]
        
        status = "✅" if detected == expected else "❌"
        print(f"{i+1}. {status} Input: '{text}'")
        print(f"   Expected: '{expected}', Got: '{detected}' (Confidence: {confidence:.2f})")
        
        if detected != expected:
            print(f"   ERROR DETECTED!")
        print("")
    
    # Test full message processing
    print("\nTESTING FULL MESSAGE PROCESSING:")
    print("--------------------------------\n")
    
    for i, case in enumerate(test_cases[:10]):  # Test first 10 cases for brevity
        text = case["text"]
        
        response = process_hebrew_message(text)
        
        print(f"{i+1}. Input: '{text}'")
        print(f"   Detected Intent: '{response['detected_intent']}'")
        print(f"   Response: '{response['text']}'")
        if 'options' in response and response['options']:
            print(f"   Options: {response['options']}")
        print("")
    
    # Test conversation flow
    print("\nTESTING CONVERSATION FLOW:")
    print("--------------------------\n")
    
    # Test appointment flow
    appointment_convo = [
        "אני רוצה לקבוע תור",
        "יום שלישי",
        "15 ביוני",
        "15:00",
        "מאשר",
        "תודה רבה"
    ]
    
    print("Appointment Flow Simulation:")
    phone = "test_phone_123"  # Simulate phone number for state tracking
    
    for i, message in enumerate(appointment_convo):
        print(f"\nUser: {message}")
        response = process_hebrew_message(message, phone)
        print(f"Bot: {response['text']}")
        if 'options' in response and response['options']:
            print(f"Options: {response['options']}")
        
        # Add flow state info if available
        if 'flow' in response and 'state' in response:
            print(f"Flow: {response['flow']}, State: {response['state']}")

if __name__ == "__main__":
    test_hebrew_nlp_comprehensive()
