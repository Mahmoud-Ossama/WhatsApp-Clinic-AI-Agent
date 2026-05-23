import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_nlp.hebrew_nlp import detect_hebrew_intent, process_hebrew_message

def test_orthopedic_hebrew_capabilities():
    """Test the specialized orthopedic capabilities in Hebrew NLP"""
    test_cases = [
        # Doctor information inquiries
        {"text": "מי דוקטור וסים?", "expected_intent": "doctor_bio"},
        {"text": "מה ההתמחות של הרופא?", "expected_intent": "doctor_bio"},
        {"text": "אני רוצה מידע על דוקטור וסים", "expected_intent": "doctor_bio"},
        
        # Injection inquiries
        {"text": "אני מעוניין בהזרקה לברך", "expected_intent": "injections"},
        {"text": "מה זה הזרקת PRP?", "expected_intent": "injections"},
        {"text": "מה ההבדל בין סטרואידים לחומצה היאלורונית?", "expected_intent": "injections"},
        
        # Post-injection concerns
        {"text": "יש לי כאב אחרי ההזרקה", "expected_intent": "post_injection"},
        {"text": "הברך נפוחה אחרי הטיפול", "expected_intent": "post_injection"},
        {"text": "מתי אמור לעבור הכאב מההזרקה?", "expected_intent": "post_injection"},
        
        # Pricing inquiries
        {"text": "כמה עולה טיפול?", "expected_intent": "pricing"},
        {"text": "מה המחיר של הזרקת חומצה היאלורונית?", "expected_intent": "pricing"},
        {"text": "האם קופת חולים מכסה את הטיפול?", "expected_intent": "insurance"},
        
        # Pediatric orthopedics
        {"text": "אני צריך בדיקת ירך לתינוק", "expected_intent": "pediatric"},
        {"text": "מתי צריך לעשות אולטרסאונד לתינוק?", "expected_intent": "pediatric"},
        
        # Disability assessments
        {"text": "אני צריך הערכת נכות לביטוח לאומי", "expected_intent": "disability"},
        {"text": "האם אתם עושים חוות דעת משפטית?", "expected_intent": "disability"},
        
        # Mixed or complex inquiries
        {"text": "יש לי כאב חזק בברך, אני מעוניין בהזרקת סטרואידים. כמה זה עולה?", "expected_intent": "injections"},
        {"text": "הברך שלי נפוחה וחמה אחרי ההזרקה. האם זה מסוכן?", "expected_intent": "post_injection"},
    ]
    
    print("=== ORTHOPEDIC HEBREW NLP TEST ===\n")
    
    for i, case in enumerate(test_cases):
        text = case["text"]
        expected = case["expected_intent"]
        
        result = detect_hebrew_intent(text)
        detected = result["intent"]
        confidence = result["confidence"]
        entities = result.get("entities", {})
        
        status = "✅" if detected == expected else "❌"
        print(f"{i+1}. {status} Input: '{text}'")
        print(f"   Expected: '{expected}', Got: '{detected}' (Confidence: {confidence:.2f})")
        
        if entities:
            print(f"   Entities detected: {entities}")
        
        # Test full response
        response = process_hebrew_message(text)
        print(f"   Response: '{response['text'][:50]}...'")
        print(f"   Options: {response.get('options', [])}")
        print("")

if __name__ == "__main__":
    test_orthopedic_hebrew_capabilities()
