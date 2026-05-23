"""
Specialized handlers for unfamiliar user inputs and fallback responses
"""
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

# Medical terminology and common symptoms for matching
MEDICAL_TERMS = {
    "אורתופדיה": ["עצם", "מפרק", "שריר", "גיד", "עמוד שדרה", "ברך", "קרסול", "ירך", "כתף"],
    "כאבים": ["כואב", "כאב", "מכאוב", "דקירות", "צריבה", "לחץ", "מתח"],
    "תנועה": ["תנועתיות", "גמישות", "נוקשות", "מוגבלות", "קושי בתנועה", "צליעה"],
    "דלקת": ["נפיחות", "אדמומיות", "חום", "נפוח", "אדום", "מודלק"],
    "טיפול": ["הזרקה", "פיזיותרפיה", "תרגילים", "ניתוח", "שיקום", "תרופות", "משככי כאבים"]
}

def identify_medical_topics(text):
    """
    Identify medical topics mentioned in user text
    
    Args:
        text (str): User input text
        
    Returns:
        list: Identified medical topics
    """
    topics = []
    
    # Check for each medical category
    for category, terms in MEDICAL_TERMS.items():
        if any(term in text.lower() for term in terms):
            topics.append(category)
    
    return topics

def extract_body_parts(text):
    """
    Extract mentioned body parts from text
    
    Args:
        text (str): User input text
        
    Returns:
        list: Identified body parts
    """
    body_parts = ["ראש", "צוואר", "גב", "כתף", "מרפק", "יד", "כף יד", "אצבע", "מותן", 
                 "ירך", "ברך", "קרסול", "כף רגל", "רגל", "עמוד שדרה", "מפרק", "שריר"]
    
    found_parts = []
    for part in body_parts:
        if part in text.lower():
            found_parts.append(part)
    
    return found_parts

def generate_relevant_suggestions(text, current_flow=None, current_state=None):
    """
    Generate relevant suggestions based on user input and conversation context
    
    Args:
        text (str): User input text
        current_flow (str, optional): Current conversation flow
        current_state (str, optional): Current state in the flow
        
    Returns:
        dict: Relevant response with suggested options
    """
    # Identify medical topics in the text
    topics = identify_medical_topics(text)
    
    # Extract body parts mentioned
    body_parts = extract_body_parts(text)
    
    # Build a customized response based on detected information
    if topics and body_parts:
        # User mentioned both medical topics and body parts
        response_text = f"אני מבין שאתה מתעניין ב{', '.join(topics)} ב{', '.join(body_parts)}. ד״ר וסים מתמחה בתחומים אלו. במה אוכל לעזור לך?"
        options = ["מידע על טיפולים", "קביעת תור", "מחירים וזמינות"]
    
    elif topics:
        # User mentioned medical topics only
        response_text = f"אני רואה שאתה מתעניין ב{', '.join(topics)}. איך אוכל לעזור לך בנושא זה?"
        options = ["מידע נוסף", "קביעת תור עם ד״ר וסים", "חזרה לתפריט"]
    
    elif body_parts:
        # User mentioned body parts only
        response_text = f"אני מבין שיש לך שאלה בנוגע ל{', '.join(body_parts)}. ד״ר וסים מתמחה בטיפול בבעיות באזורים אלו."
        options = ["אפשרויות טיפול", "קביעת תור", "מידע נוסף"]
    
    else:
        # No specific medical information detected
        response_text = "לא הצלחתי להבין בדיוק למה אתה מתכוון. אוכל לעזור לך באחד מהנושאים הבאים:"
        
        # Adjust options based on current flow
        if current_flow == "booking":
            options = ["המשך בקביעת תור", "מידע על שעות קבלה", "חזרה לתפריט"]
        elif current_flow == "catalog":
            options = ["טיפולים נפוצים", "הזרקות מפרקים", "מחירים", "קביעת תור"]
        else:
            options = ["קביעת תור", "מידע על טיפולים", "שעות פעילות", "יצירת קשר"]
    
    return {
        "text": response_text,
        "options": options
    }

def handle_out_of_scope(text):
    """
    Handle inputs that are completely out of scope for the medical bot
    
    Args:
        text (str): User input text
        
    Returns:
        dict: Response redirecting to relevant medical topics
    """
    return {
        "text": "אני מתמחה בסיוע בנושא שירותי המרפאה של ד״ר וסים, לרבות קביעת תורים ומידע על טיפולים אורתופדיים. במה אוכל לעזור לך בתחומים אלו?",
        "options": ["קביעת תור", "מידע על טיפולים", "אודות ד״ר וסים", "יצירת קשר"]
    }

def handle_unclear_input(text, confidence_score, context=None):
    """
    Main handler for unclear or unfamiliar user inputs
    
    Args:
        text (str): User input text
        confidence_score (float): Confidence score from intent detection
        context (dict, optional): Current conversation context
        
    Returns:
        dict: Appropriate response with guidance
    """
    # Check if text is very short (less than 3 words)
    words = text.split()
    if len(words) < 3:
        return {
            "text": f"האם תוכל להרחיב יותר על בקשתך? זה יעזור לי להבין טוב יותר במה אוכל לעזור לך.",
            "options": ["קביעת תור", "מידע על טיפולים", "יצירת קשר עם ד״ר וסים"]
        }
    
    # Check if input might be completely out of scope
    medical_words = sum(1 for category in MEDICAL_TERMS.values() for term in category if term in text.lower())
    if medical_words == 0 and confidence_score < 0.2:
        return handle_out_of_scope(text)
    
    # Generate relevant suggestions based on the text
    current_flow = context.get('flow') if context else None
    current_state = context.get('state') if context else None
    
    return generate_relevant_suggestions(text, current_flow, current_state)
