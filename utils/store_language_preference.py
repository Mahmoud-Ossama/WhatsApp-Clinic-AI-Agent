from dashboard.models import db
from datetime import datetime

def store_user_language_preference(phone_number, language_code):
    """Store user's language preference in the database"""
    normalized_phone = phone_number.replace('+', '').strip()
    
    # Update or create language preference
    db.user_preferences.update_one(
        {'phone': normalized_phone}, 
        {'$set': {'preferred_language': language_code, 'updated_at': datetime.utcnow()}},
        upsert=True
    )
    
    return True

def get_user_language_preference(phone_number):
    """Retrieve user's language preference"""
    normalized_phone = phone_number.replace('+', '').strip()
    
    user_pref = db.user_preferences.find_one({'phone': normalized_phone})
    if user_pref and 'preferred_language' in user_pref:
        return user_pref['preferred_language']
    
    # Default to Arabic if no preference is stored
    return 'ar'
