"""Hebrew fallback responses for common interactions"""

# Default responses when Dialogflow doesn't provide proper Hebrew
HEBREW_RESPONSES = {
    "default": {
        "text": "שלום! אני יכול לעזור לך לקבוע תור, לספק מידע על טיפולים או לענות על שאלות.",
        "options": ["קביעת תור", "מידע על טיפולים", "יצירת קשר"]
    },
    "greeting": {
        "text": "שלום! אני עוזר וירטואלי של ד״ר וסים. איך אני יכול לעזור לך היום?",
        "options": ["קביעת תור", "מידע על טיפולים", "יצירת קשר"]
    },
    "appointment": {
        "text": "לקביעת תור, אנא בחר יום מהאפשרויות.",
        "options": ["ראשון", "שלישי", "חמישי"]
    },
    "help": {
        "text": "אני יכול לעזור עם הנושאים הבאים:",
        "options": ["קביעת תור", "מידע על טיפולים", "שעות פעילות", "מיקום המרפאה"]
    }
}

def get_hebrew_response(intent_or_text):
    """Get appropriate Hebrew response based on intent name or message text"""
    # Check for specific intents or keywords in text
    text_lower = intent_or_text.lower() if isinstance(intent_or_text, str) else ""
    
    # Check for greetings
    if any(greeting in text_lower for greeting in ["שלום", "היי", "בוקר טוב", "ערב טוב"]):
        return HEBREW_RESPONSES["greeting"]
    
    # Check for appointment-related text
    if any(term in text_lower for term in ["תור", "פגישה", "מועד"]):
        return HEBREW_RESPONSES["appointment"]
    
    # Check for help/info queries
    if any(term in text_lower for term in ["עזרה", "מידע", "שאלה"]):
        return HEBREW_RESPONSES["help"]
        
    # Default response if no match
    return HEBREW_RESPONSES["default"]
