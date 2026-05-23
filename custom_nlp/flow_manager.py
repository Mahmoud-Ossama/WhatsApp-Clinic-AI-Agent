"""
Flow manager for handling conversation flow transitions
and integrating with the Hebrew NLP system.
"""
import logging
import re
import json
from datetime import datetime, timedelta
from utils.store_conversation_state import get_conversation_state, store_conversation_state
from .conversation_flows import process_flow_transition, get_flow, WELCOME_FLOW
from .hebrew_nlp import detect_hebrew_intent, HEBREW_RESPONSES, process_hebrew_text, extract_hebrew_entities

logger = logging.getLogger(__name__)

# Constants
MAX_TURNS = 10  # Maximum conversation turns before starting fresh
MAX_STATE_AGE = 30  # Maximum minutes to keep conversation context

def personalize_message(text, context):
    """Replace placeholders in messages with context values"""
    if not context:
        return text
        
    personalized = text
    
    # Replace each context variable
    for key, value in context.items():
        placeholder = "{" + key + "}"
        if placeholder in personalized:
            personalized = personalized.replace(placeholder, str(value))
            
    return personalized

def start_specific_flow(flow_name, state_name, phone_number, context=None):
    """
    Start a specific conversation flow for a user
    
    Args:
        flow_name (str): Name of the flow to start
        state_name (str): Initial state name
        phone_number (str): User's phone number for context tracking
        context (dict, optional): Initial context data
        
    Returns:
        dict: Response with text, options and flow information
    """
    flow = get_flow(flow_name)
    if not flow:
        logger.warning(f"Flow '{flow_name}' not found when trying to start specific flow")
        return {
            "text": HEBREW_RESPONSES['default']['text'],
            "options": HEBREW_RESPONSES['default']['options'],
            "error": "flow_not_found"
        }
    
    if state_name not in flow.get('states', {}):
        logger.warning(f"State '{state_name}' not found in flow '{flow_name}'")
        # Use initial state instead
        state_name = flow.get('initial_state', next(iter(flow.get('states', {}))))
    
    state_data = flow['states'][state_name]
    message = state_data.get('message', {})
    
    # Create context if not provided
    context = context or {}
    context['flow'] = flow_name
    context['state'] = state_name
    
    # Process dynamic options if needed
    if 'options' in message and isinstance(message['options'], list) and any('DYNAMIC' in str(opt) for opt in message['options']):
        from .conversation_flows import get_dynamic_options
        dynamic_options = get_dynamic_options(state_name, context)
        if dynamic_options:
            # Replace DYNAMIC placeholder with actual options
            for i, opt in enumerate(message['options']):
                if 'DYNAMIC' in str(opt):
                    message['options'] = dynamic_options
                    break
    
    # Personalize message with context variables
    if 'text' in message and context:
        message['text'] = personalize_message(message['text'], context)
    
    # Store the conversation state
    if phone_number:
        store_conversation_state(phone_number, {
            'flow': flow_name,
            'state': state_name,
            'context': context,
            'last_update': datetime.utcnow()
        })
    
    # Return the response
    return {
        "text": message.get('text', ''),
        "options": message.get('options', []),
        "flow": flow_name,
        "state": state_name
    }

def handle_flow_based_input(text, phone_number, current_flow, current_state, context=None):
    """
    Process input based on current flow and state
    
    Args:
        text (str): User's message text
        phone_number (str): User's phone number for context tracking
        current_flow (str): Current conversation flow
        current_state (str): Current state in the flow
        context (dict): Current context data
        
    Returns:
        dict: Response with text, options and updated flow information
    """
    if not current_flow or not current_state:
        # No active flow, use intent detection
        return None
    
    # Debug logging to help diagnose flow issues
    logger.debug(f"Before transition - Flow: {current_flow}, State: {current_state}, Input: '{text}'")
    logger.debug(f"Context before: {context}")
    
    # Process the transition based on user input
    next_flow, next_state, response, updated_context = process_flow_transition(
        current_flow, current_state, text, context
    )
    
    # Debug logging after transition
    logger.debug(f"After transition - Flow: {next_flow}, State: {next_state}")
    logger.debug(f"Context after: {updated_context}")
    logger.debug(f"Response: {response}")
    
    # Verify that we're not incorrectly going back to welcome flow
    if next_flow == "welcome" and current_flow != "welcome" and text not in ["חזרה לתפריט", "חזרה לתפריט הראשי", "תפריט ראשי"]:
        logger.warning(f"Unexpected transition to welcome flow detected! Staying in {current_flow}.{current_state}")
        
        # Get current state data again to recover
        from .conversation_flows import get_flow
        flow = get_flow(current_flow)
        if flow and current_state in flow.get('states', {}):
            current_state_data = flow['states'][current_state]
            response = current_state_data.get('message', {})
            next_flow = current_flow
            next_state = current_state
            
            # Add notice to user that something went wrong
            if 'text' in response:
                response['text'] = "אני מתנצל על התקלה. בוא נמשיך בתהליך.\n\n" + response['text']
    
    # Prepare the response
    if 'text' in response:
        response['text'] = personalize_message(response['text'], updated_context)
    
    # Save important context for reference
    if "subject" in updated_context or "topic" in updated_context:
        updated_context['last_topic'] = updated_context.get('subject') or updated_context.get('topic')
        
    # Store the updated conversation state
    if phone_number:
        store_conversation_state(phone_number, {
            'flow': next_flow,
            'state': next_state,
            'context': updated_context,
            'last_update': datetime.utcnow()
        })
    
    # Minimize options if needed
    if should_minimize_options(context, text) and 'options' in response and len(response['options']) > 3:
        response['options'] = limit_options_for_mid_conversation(response['options'], 3)
    
    # Return the response with flow information
    return {
        "text": response.get('text', ''),
        "options": response.get('options', []),
        "flow": next_flow,
        "state": next_state,
        "context": updated_context
    }

def is_intent_override_needed(text, current_flow, current_state):
    """
    Check if the current flow should be interrupted by a high-priority intent
    
    Args:
        text (str): User's message text
        current_flow (str): Current conversation flow
        current_state (str): Current state in the flow
        
    Returns:
        tuple: (bool, reason) - True if flow should be overridden, and reason for override
    """
    # Check for emergency keywords that should always interrupt
    emergency_keywords = ["חירום", "דחוף מאוד", "מסוכן", "סכנת חיים", "חום גבוה מאוד", "זיהום חמור"]
    if any(keyword in text.lower() for keyword in emergency_keywords):
        return True, "emergency"
    
    # Check for explicit requests to change the topic or go back
    change_topic_patterns = [
        r'\b(חזרה לתפריט|תפריט ראשי|התחל מחדש|שאלה אחרת|נושא אחר)\b',
        r'\b(אני רוצה לשאול על|אני רוצה לדעת על|תוכל לספר לי על)\b'
    ]
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in change_topic_patterns):
        return True, "change_topic"
    
    # Check for post-injection concerns that need immediate attention
    post_injection_patterns = [
        r'\b(חום גבוה|מפרק חם|נפיחות חמורה|הפרשה|מוגלה|זיהום)\b.+\b(אחרי הזרקה|לאחר הזרקה)\b',
        r'\b(אחרי הזרקה|לאחר הזרקה)\b.+\b(חום גבוה|מפרק חם|נפיחות חמורה|הפרשה|מוגלה|זיהום)\b'
    ]
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in post_injection_patterns):
        return True, "post_injection_concern"
    
    # Add tracking for conversation context switches
    context_switch_indicators = [
        r'\b(רגע|שניה|שאלה אחרת|דבר אחר|נושא אחר)\b',
        r'\b(יש לי שאלה|אני רוצה לשאול)\b'
    ]
    
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in context_switch_indicators):
        return True, "context_switch"  # Return reason for override
    
    # By default, stay within the current flow
    return False, None

def extract_flow_from_intent(intent_name):
    """
    Determine appropriate flow based on detected intent
    
    Args:
        intent_name (str): Detected intent name
        
    Returns:
        tuple: (flow_name, state_name)
    """
    intent_flow_mapping = {
        "greeting": ("welcome", "greeting"),
        "appointment_request": ("booking", "init"),  # This already points to the booking flow
        "services": ("catalog", "services"),
        "injections": ("catalog", "injections"),
        "doctor_info": ("welcome", "doctor_bio"),
        "prices": ("catalog", "pricing"),
        "pediatric": ("catalog", "pediatric"),
        "disability": ("catalog", "disability"),
        "post_injection": ("injected_patient", "check_status"),
        "emergency": ("injected_patient", "urgent_contact"),
        "patient_inquiry": ("new_patient", "inquiry")
    }
    return intent_flow_mapping.get(intent_name, ("welcome", "greeting"))

def get_debug_info(response, original_text=None, intent_info=None):
    """
    Add debug information to the response
    
    Args:
        response (dict): Existing response
        original_text (str, optional): Original user input
        intent_info (dict, optional): Intent detection information
        
    Returns:
        dict: Response with debug information
    """
    # Only add debug info if not already present
    if "debug_info" not in response:
        debug_info = {}
        if original_text:
            debug_info["original_text"] = original_text
        if intent_info:
            debug_info["intent"] = intent_info.get("intent")
            debug_info["confidence"] = intent_info.get("confidence")
            debug_info["entities"] = intent_info.get("entities", {})
        if "flow" in response:
            debug_info["flow"] = response["flow"]
            debug_info["state"] = response.get("state")
        
        response["debug_info"] = debug_info
    
    return response

def process_patient_complaint(text, phone_number=None):
    """
    Process incoming patient complaints and start the new patient flow
    
    Args:
        text (str): Patient's complaint text
        phone_number (str, optional): Patient's phone number
        
    Returns:
        dict: Response with appropriate next steps
    """
    # Extract potential symptoms from text
    complaint_type = "תלונות"
    # Look for specific complaints in the text
    if any(term in text.lower() for term in ["גב", "צוואר", "צואר", "כתף"]):
        complaint_type = "כאבי גב/צוואר"
    elif any(term in text.lower() for term in ["ברך", "ברכיים", "מפרק", "מרפק", "ירך"]):
        complaint_type = "כאבי מפרקים"
    elif any(term in text.lower() for term in ["דיסק", "פריצת", "פריצה"]):
        complaint_type = "פריצת דיסק"
    elif any(term in text.lower() for term in ["שבר", "נפילה", "תאונה", "פציעה"]):
        complaint_type = "טראומה/שבר"
    
    # Start the new patient flow with the complaint context
    context = {"complaint_type": complaint_type, "initial_message": text}
    return start_specific_flow("new_patient", "inquiry", phone_number, context)

def is_mid_conversation(context):
    """Determine if user is in the middle of a conversation flow"""
    if not context:
        return False
    
    # Check interaction count if available
    interaction_count = context.get('interaction_count', 0)
    if interaction_count > 2:
        return True
    
    # Check conversation depth by state transitions
    state_history = context.get('state_history', [])
    if len(state_history) >= 2:
        return True
    
    # Check if in the middle of a specific topic
    if context.get('current_topic') or context.get('last_topic'):
        return True
        
    return False

def limit_options_for_mid_conversation(options, max_options=3):
    """Reduce number of options during mid-conversation to avoid button overload"""
    if not options or len(options) <= max_options:
        return options
    
    # Keep important options that should always be present
    important_options = ["יצירת קשר", "חזרה לתפריט", "סיום שיחה"]
    critical_options = [opt for opt in options if any(imp in opt for imp in important_options)]
    
    # Get non-critical options
    regular_options = [opt for opt in options if opt not in critical_options]
    
    # Determine how many regular options we can keep
    remaining_slots = max_options - len(critical_options)
    if remaining_slots <= 0:
        # If we have too many critical options, just return them (truncated if needed)
        return critical_options[:max_options]
    
    # Return a mix of regular and critical options
    return regular_options[:remaining_slots] + critical_options

def should_minimize_options(context, text):
    """Determine if we should minimize options in response"""
    # If already deep in conversation, minimize options
    if is_mid_conversation(context):
        return True
    
    # If user asks a specific question, minimize options
    question_markers = ["?", "מה", "איך", "למה", "מתי", "האם", "כמה"]
    if any(marker in text for marker in question_markers):
        return True
    
    # If asking for specific details about a topic
    topic_detail_patterns = [
        r'מידע על \w+',
        r'פרטים על \w+',
        r'הסבר על \w+',
        r'מהי \w+',
        r'מה זה \w+'
    ]
    if any(re.search(pattern, text) for pattern in topic_detail_patterns):
        return True
    
    return False

def handle_ambiguous_input(text, intent_info, context):
    """Request clarification when input could match multiple intents"""
    confidence = intent_info.get("confidence", 0)
    intent = intent_info.get("intent", "unknown")
    
    # If we have low confidence but multiple potential matches
    if 0.2 <= confidence <= 0.4:
        # Get the top 2-3 potential intents
        potential_intents = get_potential_intents(text)
        if len(potential_intents) >= 2:
            options = []
            for pot_intent in potential_intents[:3]:
                if pot_intent == "appointment_request":
                    options.append("קביעת תור באתר")  # Updated text to mention the website
                elif pot_intent == "services":
                    options.append("מידע על טיפולים")
                elif pot_intent == "medical_concern":
                    options.append("שאלה רפואית")
                elif pot_intent == "injections":
                    options.append("מידע על הזרקות")
                elif pot_intent == "prices":
                    options.append("מידע על מחירים")
            
            if options:
                return {
                    "text": "למה בדיוק התכוונת? אנא בחר אחת מהאפשרויות:",
                    "options": options,
                    "ambiguous_input": text
                }
    
    return None

def get_potential_intents(text):
    """Get multiple potential intents for ambiguous text"""
    # This would be implemented to return intent names that had close match scores
    from custom_nlp.hebrew_nlu import understand_hebrew_text
    
    potential_intents = []
    result = understand_hebrew_text(text)
    potential_intents.append(result["intent"])
    
    # Add other potential intents based on keyword matching
    keywords_to_intents = {
        "תור": "appointment_request",
        "מועד": "appointment_request",
        "פגישה": "appointment_request",
        "מידע": "services",
        "מחיר": "prices",
        "כאב": "medical_concern",
        "הזרקה": "injections",
        "זריקה": "injections",
        "עלות": "prices",
        "רופא": "doctor_info",
        "טיפול": "services"
    }
    
    for keyword, intent in keywords_to_intents.items():
        if keyword in text and intent not in potential_intents:
            potential_intents.append(intent)
    
    return potential_intents

def handle_post_injection_flow(sender_id, text, context=None):
    """
    Special handling for patients reporting symptoms after injections
    
    Args:
        sender_id (str): User's identifier
        text (str): User's message
        context (dict): Current conversation context
        
    Returns:
        dict: Response with appropriate guidance
    """
    context = context or {}
    
    # Check for urgent symptoms
    urgent_symptoms = [
        "חום גבוה", "מפרק חם", "נפיחות גדולה", "הפרשה", "מוגלה", 
        "אודם משמעותי", "כאב חזק", "לא יכול להזיז"
    ]
    
    urgent_detected = any(symptom in text.lower() for symptom in urgent_symptoms)
    
    if urgent_detected:
        # Critical symptoms detected - recommend immediate contact
        return {
            "text": "התסמינים שתיארת מצריכים התייחסות רפואית מיידית! אנא צור קשר עם ד״ר וסים בהקדם בטלפון 0537330702 או פנה לחדר מיון אם המצב חמור.",
            "options": ["אתקשר עכשיו", "תודה על המידע"],
            "detected_intent": "post_injection_urgent",
            "format": "simple",  # Use simple format for important medical information
            "priority": "high"
        }
    else:
        # Normal post-injection symptoms
        return {
            "text": "כאב ואי-נוחות מסוימים לאחר הזרקה הם תופעה נורמלית וצפויה. מומלץ:\n\n• לנוח ולהמנע מפעילות מאומצת ל-24-48 שעות\n• להניח קרח על האזור למשך 15-20 דקות מספר פעמים ביום\n• ליטול משככי כאבים כמו אקמול לפי הצורך\n\nרוב תופעות הלוואי חולפות תוך 1-2 ימים. אם הכאב חריף או נמשך מעבר לכך, או אם מופיעים סימנים כמו חום, אודם משמעותי או נפיחות גדולה, אנא צור קשר עם המרפאה.",
            "options": ["תודה על המידע", "מתי לפנות לרופא", "קביעת תור למעקב"],
            "detected_intent": "post_injection_normal",
            "format": "simple",
            "priority": "medium"
        }

def process_hebrew_flow(text, sender_id):
    """
    Main entry point for Hebrew message processing with conversation flow management
    
    Args:
        text (str): User's message text
        sender_id (str): User's identifier
        
    Returns:
        dict: Response object with text, options, and metadata
    """
    try:
        logger.debug(f"Processing Hebrew flow for user {sender_id}: '{text[:30]}...'")
        
        # Get current conversation state
        state_data = get_conversation_state(sender_id) or {}
        logger.debug(f"Retrieved state for {sender_id}: {state_data}")
        
        # Extract key variables from state
        context = state_data.get('context', {})
        current_flow = state_data.get('current_flow', 'main')
        current_step = state_data.get('current_step', 'init')
        turn_count = state_data.get('turn_count', 0)
        
        # Process the text to get intent and entities
        basic_response = process_hebrew_text(text, sender_id)
        
        # Get detected intent details
        intent = basic_response.get('detected_intent', 'unknown')
        confidence = basic_response.get('confidence', 0.0)
        entities = basic_response.get('entities', {})
        
        # Handle flow transitions when user asks a different question
        if intent == 'hours' and current_flow != 'hours':
            # User asked about hours, switch to hours flow
            response = {
                "text": "שעות הפעילות של ד\"ר וסים הן:\n\nיום שני: 18:00-20:00\nיום רביעי: 17:00-20:00\nיום שישי: 14:00-17:00\n\nהמרפאה נמצאת ברהט, במתחם מיון קדמי שכ 4 בית 150",
                "options": ["חזור לתפריט הראשי", "קביעת תור"],
                "detected_intent": intent
            }
            
            # Update state
            new_state = {
                'current_flow': 'hours',
                'current_step': 'info',
                'context': context,
                'turn_count': turn_count + 1,
                'last_update': datetime.utcnow()
            }
            
            store_conversation_state(sender_id, new_state)
            logger.debug(f"Updated state for {sender_id} to hours flow: {new_state}")
            return response
            
        # Check for option selection in the booking flow
        if current_flow == 'booking' and current_step == 'treatment_selection':
            # Check if user selected a treatment type
            if any(treatment in text.lower() for treatment in ["כאבי גב", "גב", "כאבי ברכיים", "ברכיים", "כאבי כתף", "כתף", "הזרקות"]):
                treatment_type = None
                if "גב" in text.lower():
                    treatment_type = "כאבי גב"
                elif "ברכיים" in text.lower():
                    treatment_type = "כאבי ברכיים"
                elif "כתף" in text.lower():
                    treatment_type = "כאבי כתף"
                elif "הזרקות" in text.lower():
                    treatment_type = "הזרקות"
                elif "אחר" in text.lower():
                    treatment_type = "אחר"
                
                if treatment_type:
                    # Redirect to website for booking
                    response = {
                        "text": f"לקביעת תור ל{treatment_type}, אנא בקר באתר הרשמי של ד\"ר וסים:\nhttps://www.wasem.co.il/\n\nאו התקשר ישירות למרפאה: 0523065599",
                        "options": ["חזור לתפריט הראשי", "מידע על טיפולים", "שעות פעילות"],
                        "detected_intent": intent,
                        "flow": "booking",
                        "step": "redirect_to_website"
                    }
                    
                    # Update state
                    new_state = {
                        'current_flow': 'main',
                        'current_step': 'init',
                        'context': {**context, 'treatment_type': treatment_type, 'referred_to_website': True},
                        'turn_count': turn_count + 1,
                        'last_update': datetime.utcnow()
                    }
                    
                    store_conversation_state(sender_id, new_state)
                    logger.debug(f"Updated state for {sender_id} to redirect to website: {new_state}")
                    return response
        
        # Generate a response based on the flow state and detected intent
        response = handle_hebrew_flow(
            text, 
            intent, 
            confidence,
            entities, 
            sender_id, 
            current_flow, 
            current_step, 
            context, 
            turn_count
        )
        
        # Return the processed response
        return response
        
    except Exception as e:
        logger.error(f"Error in Hebrew flow manager: {str(e)}", exc_info=True)
        # Fallback response in case of error
        return {
            "text": "מצטער, התרחשה שגיאה בעיבוד הבקשה שלך. אנא נסה שוב או צור קשר ישירות עם המרפאה בטלפון 0537330702.",
            "options": ["נסה שוב", "צור קשר"],
            "detected_intent": "error",
            "format": "simple"
        }

def handle_hebrew_flow(text, intent, confidence, entities, sender_id, current_flow, current_step, context, turn_count):
    """
    Process the user message based on current flow state and intent
    
    Args:
        text (str): User's message
        intent (str): Detected intent
        confidence (float): Confidence score
        entities (dict): Extracted entities
        sender_id (str): User's identifier
        current_flow (str): Current conversation flow
        current_step (str): Current step in the flow
        context (dict): Conversation context
        turn_count (int): Number of turns in this conversation
        
    Returns:
        dict: Response object
    """
    try:
        # Initialize response
        response = {}
        
        # If user is starting a new conversation with a greeting
        if intent == "greeting" and current_step == "init":
            response = {
                "text": "שלום! אני העוזר הווירטואלי של ד״ר וסים. איך אוכל לעזור לך היום?",
                "options": ["קביעת תור", "מידע על טיפולים", "מחירים", "שעות פעילות"],
                "detected_intent": "greeting"
            }
            
            # Update state
            new_state = {
                'current_flow': 'main',
                'current_step': 'menu',
                'context': context,
                'turn_count': turn_count + 1,
                'last_update': datetime.utcnow()
            }
            
            store_conversation_state(sender_id, new_state)
            logger.debug(f"Updated state for {sender_id} to {new_state}")
            
            return response
            
        # If user wants to book an appointment
        elif intent == "booking" or "קביעת תור" in text or (current_flow == 'booking' and current_step != 'complete'):
            # Move to booking flow
            response = {
                "text": "לקביעת תור אצל ד״ר וסים, אנא בחר את סוג הטיפול שאתה מעוניין בו:",
                "options": ["כאבי גב", "כאבי ברכיים", "כאבי כתף", "הזרקות", "אחר"],
                "detected_intent": "booking"
            }
            
            # Update state to booking flow
            new_state = {
                'current_flow': 'booking',
                'current_step': 'treatment_selection',
                'context': {**context, 'booking_started': True},
                'turn_count': turn_count + 1,
                'last_update': datetime.utcnow()
            }
            
            store_conversation_state(sender_id, new_state)
            logger.debug(f"Updated state for {sender_id} to booking flow: {new_state}")
            
            return response
        
        # If user is asking about prices
        elif intent == "pricing" or "מחיר" in text.lower() or "עלות" in text.lower() or "כמה עולה" in text.lower():
            # User asked about pricing, provide the accurate pricing information
            response = {
                "text": "עלות הטיפול היעוץ והטיפול הרפואי הוא 400 ש״ח.\nהמחיר אינו כולל עלות חומרים להזרקה או הערכות נכות וחוות דעת משפטיות.",
                "options": ["חזור לתפריט הראשי", "קביעת תור", "שעות פעילות"],
                "detected_intent": "pricing"
            }
            
            # Update state
            new_state = {
                'current_flow': 'pricing',
                'current_step': 'info',
                'context': context,
                'turn_count': turn_count + 1,
                'last_update': datetime.utcnow()
            }
            
            store_conversation_state(sender_id, new_state)
            logger.debug(f"Updated state for {sender_id} to pricing flow: {new_state}")
            return response
        
        # Default response if we don't understand or can't progress the flow
        response = {
            "text": "אני יכול לעזור לך בקביעת תור, לתת מידע על הטיפולים שלנו, או לענות על שאלות. במה אוכל לעזור?",
            "options": ["קביעת תור", "מידע על טיפולים", "שעות פעילות", "צור קשר"],
            "detected_intent": intent
        }
        
        # Update the turn count anyway
        new_state = {
            'current_flow': current_flow,
            'current_step': current_step,
            'context': context,
            'turn_count': turn_count + 1,
            'last_update': datetime.utcnow()
        }
        
        store_conversation_state(sender_id, new_state)
        return response
            
    except Exception as e:
        logger.error(f"Error handling Hebrew flow: {str(e)}", exc_info=True)
        return {
            "text": "מצטער, התרחשה שגיאה. אנא נסה שוב או צור קשר ישירות עם המרפאה בטלפון 0537330702.",
            "options": ["נסה שוב", "צור קשר"],
            "detected_intent": "error"
        }

def get_historical_context(phone_number):
    """Retrieve important historical context even from expired sessions"""
    try:
        from dashboard.models import db
        
        # Find the most recent conversation with this user
        recent_contexts = list(db.conversation_contexts.find(
            {"phone_number": phone_number},
            sort=[("last_update", -1)],
            limit=5  # Look at last 5 conversations
        ))
        
        if not recent_contexts:
            return {}
            
        # Extract meaningful context that should persist
        important_context = {}
        for ctx in recent_contexts:
            context_data = ctx.get("context", {})
            
            # Save topics discussed
            if "current_topic" in context_data and "current_topic" not in important_context:
                important_context["last_topic"] = context_data["current_topic"]
                
            # Save appointment information
            if "selected_date" in context_data and "last_appointment" not in important_context:
                important_context["last_appointment"] = {
                    "date": context_data.get("selected_date"),
                    "time": context_data.get("selected_time"),
                }
                
            # Save patient complaints or symptoms
            if "complaint_type" in context_data and "patient_complaint" not in important_context:
                important_context["patient_complaint"] = context_data["complaint_type"]
            
            # Save injection status if present
            if "injection_received" in context_data and "injection_received" not in important_context:
                important_context["injection_received"] = context_data["injection_received"]
                important_context["injection_date"] = context_data.get("injection_date")
                important_context["injection_type"] = context_data.get("injection_type")
        
        return important_context
    except Exception as e:
        logger.error(f"Error getting historical context: {e}")
        return {}