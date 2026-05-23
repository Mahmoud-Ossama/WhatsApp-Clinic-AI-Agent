"""
Context management utilities for maintaining conversation state
and ensuring coherent, continuous conversations.
"""
import logging
from datetime import datetime
from utils.store_conversation_state import store_conversation_state, get_conversation_state

logger = logging.getLogger(__name__)

def update_conversation_context(phone_number, updates, replace=False):
    """
    Update the conversation context with new information
    
    Args:
        phone_number (str): User's phone number
        updates (dict): New context values to add/update
        replace (bool): If True, replace entire context instead of updating
        
    Returns:
        dict: Updated context
    """
    if not phone_number:
        return updates
        
    # Get existing context
    existing = get_conversation_state(phone_number)
    context = existing.get('context', {}) if existing else {}
    
    # Update or replace
    if replace:
        context = updates
    else:
        context.update(updates)
    
    # Add metadata
    context['last_updated'] = datetime.now().isoformat()
    
    # Store back
    store_conversation_state(phone_number, existing.get('state') if existing else None, context)
    
    return context

def track_conversation_topic(context, new_topic=None, topic_source=None):
    """
    Track conversation topics for better context management
    
    Args:
        context (dict): Current conversation context
        new_topic (str, optional): New topic being discussed
        topic_source (str, optional): Source of the topic (user, system, etc.)
        
    Returns:
        dict: Updated context with topic tracking
    """
    # Initialize topic tracking if needed
    if 'topic_history' not in context:
        context['topic_history'] = []
    
    # If we have a new topic that's different from current
    if new_topic and (not context.get('current_topic') or context['current_topic'] != new_topic):
        # Save current topic to history
        if context.get('current_topic'):
            context['topic_history'].append({
                'topic': context['current_topic'],
                'timestamp': datetime.now().isoformat(),
                'source': topic_source or 'unknown'
            })
        
        # Set new current topic
        context['current_topic'] = new_topic
        context['topic_source'] = topic_source or 'system'
        context['topic_start_time'] = datetime.now().isoformat()
    
    return context

def should_provide_direct_information(text, context):
    """
    Determine if we should provide direct information rather than buttons
    
    Args:
        text (str): User's message 
        context (dict): Current conversation context
        
    Returns:
        tuple: (should_provide_direct, topic)
    """
    # Check for question markers
    question_indicators = ["?", "מה", "איך", "למה", "מתי", "האם", "כמה", "מי"]
    is_question = any(indicator in text for indicator in question_indicators)
    
    # Check for direct treatment references
    treatments = {
        "פלזמה": "PRP",
        "PRP": "PRP",
        "סטרואידים": "steroids",
        "חומצה היאלורונית": "hyaluronic",
        "היאלורונית": "hyaluronic",
        "אולטרסאונד": "ultrasound"
    }
    
    # Look for exact treatment selection from options
    for treatment, topic in treatments.items():
        # Direct selection of treatment option
        if treatment == text.strip():
            return True, topic
        
        # Question about treatment
        if treatment in text and is_question:
            return True, topic
    
    # If we've recently discussed a topic and user asks a follow-up
    if context.get('current_topic') and is_question:
        return True, context['current_topic']
    
    return False, None
