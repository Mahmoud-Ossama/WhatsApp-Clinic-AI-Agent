def detect_message_language(text):
    """
    Detect the language of a message based on its characters.
    
    Args:
        text (str): The text message to analyze
        
    Returns:
        str: Language code - 'ar' for Arabic, 'he' for Hebrew, 'en' for English
    """
    # Count characters in different ranges
    hebrew_chars = sum(1 for c in text if '\u0590' <= c <= '\u05FF')
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    
    # More sophisticated detection - check which script has more characters
    if hebrew_chars > 0 and hebrew_chars >= arabic_chars:
        return "he"
    elif arabic_chars > 0:
        return "ar"
    elif any('a' <= c.lower() <= 'z' for c in text):
        return "en"
    
    # If no clear script is detected, default to Arabic
    return "ar"

def should_override_language_preference(text):
    """
    Check if the message text explicitly requests a language change.
    
    Args:
        text (str): The message text to analyze
        
    Returns:
        tuple: (should_override, language_code)
    """
    # Check for explicit language change requests in the message
    lower_text = text.lower()
    
    # Check for Hebrew requests
    if any(term in lower_text for term in ['hebrew', 'עברית', 'בעברית']):
        return True, 'he'
    
    # Check for Arabic requests
    if any(term in lower_text for term in ['arabic', 'العربية', 'بالعربية']):
        return True, 'ar'
    
    # No override needed
    return False, None

def get_nationality_from_language(language_code):
    """
    Convert language code to nationality label used in our system.
    
    Args:
        language_code (str): 'ar', 'he', or 'en'
        
    Returns:
        str: 'arab' or 'israeli'
    """
    if language_code == 'he':
        return 'israeli'
    else:
        return 'arab'  # Default to Arab for all other languages

def get_language_from_nationality(nationality):
    """
    Convert nationality to language code.
    
    Args:
        nationality (str): 'arab' or 'israeli'
        
    Returns:
        str: 'ar' or 'he'
    """
    if nationality in ['israeli', 'hebrew']:
        return 'he'
    else:
        return 'ar'

def get_user_language_preference(phone_number):
    """
    Retrieve user's language preference from the database.
    
    Args:
        phone_number (str): User's phone number
        
    Returns:
        str: Language code ('ar' or 'he')
    """
    # Import here to avoid circular imports
    from utils.store_language_preference import get_user_language_preference as get_preference
    
    try:
        # Call the actual implementation from store_language_preference
        return get_preference(phone_number)
    except Exception as e:
        # If any error occurs, default to Arabic
        import logging
        logging = logging.getLogger(__name__)
        logging.error(f"Error retrieving language preference: {str(e)}")
        return 'ar'
