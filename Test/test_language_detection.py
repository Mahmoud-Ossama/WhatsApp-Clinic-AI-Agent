import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.language_utils import detect_message_language

def test_language_detection():
    """Test the language detection function with different scripts"""
    test_cases = [
        ("مرحبا كيف حالك؟", "ar", "Arabic text"),
        ("שלום, מה שלומך?", "he", "Hebrew text"),
        ("Hello, how are you?", "en", "English text"),
        ("مرحبا Hello", "ar", "Mixed Arabic-English"),
        ("שלום Hello", "he", "Mixed Hebrew-English"),
        ("123456", "ar", "Numbers only (should default to Arabic)"),
        ("!@#$%^", "ar", "Symbols only (should default to Arabic)"),
        ("مرحبا שלום", "ar", "Mixed Arabic-Hebrew (Arabic should win)"),
    ]
    
    print("=== LANGUAGE DETECTION TEST ===\n")
    
    for text, expected, description in test_cases:
        result = detect_message_language(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} {description}:")
        print(f"   Text: '{text}'")
        print(f"   Expected: '{expected}', Got: '{result}'")
        
        # Print character codes for debugging
        codes = ", ".join([f"{c}:{ord(c):x}" for c in text[:10]])
        print(f"   Character codes: {codes}\n")

if __name__ == "__main__":
    test_language_detection()
