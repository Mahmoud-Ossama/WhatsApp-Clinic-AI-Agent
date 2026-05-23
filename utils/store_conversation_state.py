"""
Functions for storing and retrieving conversation state in MongoDB.
This allows conversations to maintain context between messages.
"""
import logging
from datetime import datetime, timedelta
from dashboard.models import db
import json

logger = logging.getLogger(__name__)

def store_conversation_state(phone_number, state_data):
    """
    Store conversation state for a user
    
    Args:
        phone_number (str): User's phone number
        state_data (dict): State data to store
    """
    try:
        # Normalize phone number (remove 'whatsapp:' prefix if present)
        phone_number = phone_number.replace('whatsapp:', '').strip()
        
        # Add timestamp
        if isinstance(state_data, dict):
            if 'last_update' not in state_data:
                state_data['last_update'] = datetime.utcnow()
        else:
            state_data = {
                'state': state_data,
                'last_update': datetime.utcnow()
            }
        
        # Update or create state document
        db.conversation_contexts.update_one(
            {'phone_number': phone_number},
            {'$set': state_data},
            upsert=True
        )
        
        logger.debug(f"Stored conversation state for {phone_number}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing conversation state: {str(e)}", exc_info=True)
        return False

def get_conversation_state(phone_number):
    """
    Retrieve conversation state for a user
    
    Args:
        phone_number (str): User's phone number
        
    Returns:
        dict: User's conversation state, or empty dict if not found or expired
    """
    try:
        # Normalize phone number (remove 'whatsapp:' prefix if present)
        phone_number = phone_number.replace('whatsapp:', '').strip()
        
        # Find state document
        state = db.conversation_contexts.find_one({'phone_number': phone_number})
        
        if state:
            # Check if the state is too old (more than 30 minutes)
            last_update = state.get('last_update')
            if last_update:
                # Convert string timestamp to datetime if needed
                if isinstance(last_update, str):
                    try:
                        last_update = datetime.fromisoformat(last_update)
                    except ValueError:
                        # Handle old format dates or invalid dates
                        last_update = datetime.utcnow() - timedelta(minutes=5)
                
                time_diff = datetime.utcnow() - last_update
                if time_diff.total_seconds() > 1800:  # 30 minutes in seconds
                    logger.debug(f"Conversation state expired for {phone_number}")
                    return {}
            
            logger.debug(f"Retrieved conversation state for {phone_number}")
            return state
        
        logger.debug(f"No conversation state found for {phone_number}")
        return {}
        
    except Exception as e:
        logger.error(f"Error retrieving conversation state: {str(e)}", exc_info=True)
        return {}

def clear_conversation_state(phone_number):
    """
    Clear conversation state for a user
    
    Args:
        phone_number (str): User's phone number
    """
    try:
        # Normalize phone number
        phone_number = phone_number.replace('whatsapp:', '').strip()
        
        # Delete state document
        result = db.conversation_contexts.delete_one({'phone_number': phone_number})
        
        if result.deleted_count > 0:
            logger.debug(f"Cleared conversation state for {phone_number}")
        else:
            logger.debug(f"No conversation state found to clear for {phone_number}")
            
    except Exception as e:
        logger.error(f"Error clearing conversation state: {str(e)}")
