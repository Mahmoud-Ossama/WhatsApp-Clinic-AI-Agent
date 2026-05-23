import logging
from datetime import datetime, timedelta
import re
import random

logger = logging.getLogger(__name__)

# Greeting variations to make responses feel more natural
GREETINGS = [
    "שלום!",
    "היי!",
    "בוקר טוב!",
    "אהלן!",
    "שלום שלום!",
    "ברוך הבא!",
]

# Response variations to make conversation feel natural
RESPONSE_VARIATIONS = {
    "confirm": [
        "מצוין!",
        "נהדר!",
        "מעולה!",
        "יופי!",
        "מושלם!",
    ],
    "understand": [
        "אני מבין.",
        "ברור.",
        "כמובן.",
        "אוקיי, הבנתי.",
    ],
    "sorry": [
        "אני מצטער.",
        "סליחה על כך.",
        "מתנצל.",
        "סליחה.",
    ],
    "thanks": [
        "תודה רבה!",
        "תודה לך!",
        "מודה לך!",
        "תודה!",
    ]
}

def format_date_hebrew(date_str):
    """Format date string to Hebrew format"""
    try:
        if isinstance(date_str, str):
            # Parse the date string (assuming DD/MM format)
            parts = date_str.split('/')
            if len(parts) >= 2:
                day = int(parts[0])
                month = int(parts[1])
                dt_obj = datetime(datetime.now().year, month, day)
                
                # Hebrew months
                hebrew_months = [
                    "ינואר", "פברואר", "מרץ", "אפריל", "מאי", "יוני",
                    "יולי", "אוגוסט", "ספטמבר", "אוקטובר", "נובמבר", "דצמבר"
                ]
                
                # Format: "יום רביעי, ה-15 ביוני"
                day_names = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]
                day_name = day_names[dt_obj.weekday()]
                hebrew_month = hebrew_months[dt_obj.month - 1]
                
                return f"יום {day_name}, ה-{day} ב{hebrew_month}"
        
        # If any error or not a string, return as is
        return date_str
        
    except Exception as e:
        logger.error(f"Error formatting date: {e}")
        return date_str

def format_time_hebrew(time_str):
    """Format time string to Hebrew format"""
    try:
        # Check if it's already formatted with Hebrew time period
        hebrew_periods = ["בבוקר", "בצהריים", "אחה\"צ", "בערב", "בלילה"]
        if any(period in time_str for period in hebrew_periods):
            return time_str
            
        # Regular HH:MM format
        if ":" in time_str:
            hour, minute = time_str.split(":")
            hour = int(hour)
            
            # Add appropriate time period based on hour
            if 5 <= hour < 12:
                suffix = "בבוקר"
            elif 12 <= hour < 16:
                suffix = "בצהריים"
            elif 16 <= hour < 18:
                suffix = "אחה\"צ"
            elif 18 <= hour < 22:
                suffix = "בערב"
            else:
                suffix = "בלילה"
                
            # Format with Hebrew time period
            if minute == "00":
                return f"{hour} {suffix}"
            else:
                return f"{hour}:{minute} {suffix}"
        
        return time_str
        
    except Exception as e:
        logger.error(f"Error formatting time: {e}")
        return time_str

def add_variation(text, variation_type=None):
    """Add natural language variations to make responses more human-like"""
    # Add greeting variation at the beginning if applicable
    if variation_type == "greeting":
        greeting = random.choice(GREETINGS)
        return f"{greeting} {text}"
    
    # Add confirmations or understanding phrases
    if variation_type and variation_type in RESPONSE_VARIATIONS:
        variation = random.choice(RESPONSE_VARIATIONS[variation_type])
        return f"{variation} {text}"
    
    # No variation
    return text

def personalize_message(text, context):
    """Replace placeholders with context values and format dates/times"""
    if not context:
        return text
        
    # Copy the text to avoid modifications to original
    personalized = text
    
    # Replace context variables
    for key, value in context.items():
        placeholder = "{" + key + "}"
        if placeholder in personalized:
            # Format special types
            if 'date' in key and isinstance(value, str):
                value = format_date_hebrew(value)
            elif 'time' in key and isinstance(value, str):
                value = format_time_hebrew(value)
                
            personalized = personalized.replace(placeholder, str(value))
    
    return personalized

def generate_appointment_confirmation(context):
    """Generate a natural appointment confirmation message"""
    # Example context: {"selected_day": "שלישי", "selected_date": "15/06", "selected_time": "15:00"}
    
    day = context.get('selected_day', '')
    date = format_date_hebrew(context.get('selected_date', ''))
    time = format_time_hebrew(context.get('selected_time', ''))
    
    confirmation = (
        f"{random.choice(RESPONSE_VARIATIONS['confirm'])} "
        f"התור שלך נקבע ל{day}, {date} בשעה {time}. "
        f"נשלח לך הודעת אישור עם פרטי התור. "
        f"נשמח לראותך!"
    )
    
    return confirmation

def generate_expanded_information(topic, context=None):
    """
    Generate detailed information on medical topics when user asks for more details
    
    Args:
        topic (str): Topic to explain in detail
        context (dict): Optional context for personalization
        
    Returns:
        str: Detailed explanation text
    """
    expanded_info = {
        "הזרקת סטרואידים": """
הזרקת סטרואידים (קורטיקוסטרואידים) היא טיפול שמטרתו להפחית דלקת וכאב במפרק.

כיצד זה עובד:
הסטרואידים מפחיתים דלקת באזור המוזרק ע"י דיכוי פעילות מערכת החיסון המקומית. זה מפחית את הנפיחות, החום והכאב.

יתרונות:
• מהירות השפעה - הקלה מתחילה בתוך 24-48 שעות
• יעילות גבוהה בהפחתת דלקת חריפה
• עלות נמוכה יחסית
• פרוצדורה קצרה וזמינה

חסרונות:
• ההשפעה זמנית, בד"כ בין שבועיים לחודשיים
• שימוש חוזר עלול להחליש את הרקמות ולגרום לנזק ארוך טווח
• יכול להשפיע על רמות הסוכר בחולי סוכרת
• עלול להשפיע על לחץ הדם

אחרי ההזרקה:
• כאב קל הוא תגובה נורמלית ויכול להימשך 1-2 ימים
• יש להימנע מפעילות מאומצת ל-48 שעות
• מומלץ לקרר את האזור אם מופיעה נפיחות

ד"ר וסים יתאים את הטיפול למצבך הרפואי האישי ויציע חלופות במידת הצורך.
        """,
        
        "חומצה היאלורונית": """
הזרקת חומצה היאלורונית (ויסקוסופלמנטציה) מחזירה נוזל סיכה טבעי למפרקים.

כיצד זה עובד:
החומצה ההיאלורונית היא חומר טבעי בנוזל המפרקים שלנו. היא פועלת כחומר סיכה ובולם זעזועים. עם הגיל וכתוצאה מבלאי, כמות החומר מתמעטת. ההזרקה מחזירה את הנוזל למפרק ומשפרת את תנועתיות המפרק.

יתרונות:
• אפקט ארוך טווח - 6 חודשים עד שנה
• טבעי יותר מסטרואידים עם פחות תופעות לוואי
• יעיל במיוחד בשלבים מוקדמים של אוסטאוארטריטיס (בלאי מפרקים)
• עוזר לשפר את איכות הנוזל הטבעי במפרק

חסרונות:
• השפעה איטית יותר - שיפור מלא מורגש אחרי 3-4 שבועות
• יקר יותר מסטרואידים
• פחות יעיל באופן מיידי לדלקת חריפה
• לא מתאים לכל המפרקים

ישנם מספר סוגים של חומצה היאלורונית, ותוכניות הטיפול משתנות בהתאם למצב הספציפי שלך. ד"ר וסים יוכל להמליץ על הסוג המתאים ביותר למצבך.

ד"ר וסים משתמש בהזרקות מונחות במידת הצורך, לדיוק מרבי ולהפחתת אי-נוחות במהלך הטיפול.
        """,
        
        "טיפול PRP": """
טיפול בפלזמה עשירת טסיות (PRP) הוא טיפול חדשני המשתמש ביכולת הריפוי הטבעית של הגוף.

כיצד זה עובד:
1. נלקחת דגימת דם מהמטופל עצמו
2. הדם עובר סירכוז (סיבוב במהירות גבוהה) כדי להפריד את הטסיות
3. הפלזמה העשירה בטסיות מוזרקת לאזור הפגוע
4. הטסיות משחררות גורמי צמיחה שמעודדים ריפוי טבעי של הרקמות

יתרונות:
• טיפול טבעי המשתמש ברקמות של המטופל עצמו
• סיכון נמוך לתגובות אלרגיות
• עוזר לחדש רקמות ולא רק להפחית סימפטומים
• אפקט ארוך טווח שיכול להימשך שנה או יותר
• מתאים גם למטופלים שלא הגיבו לטיפולים אחרים

חסרונות:
• יקר יותר מטיפולים אחרים
• התוצאות הן הדרגתיות ולוקח זמן לראות השפעה מלאה
• לא בהכרח מכוסה על ידי קופות החולים
• נדרשות לעיתים מספר הזרקות לאפקט מיטבי

הטיפול אופטימלי ל:
• בעיות גידים כרוניות (טנדיניטיס)
• קרעים קלים ברצועות
• אוסטאוארטריטיס בשלב בינוני
• פציעות ספורט

ד"ר וסים הוא מומחה בטכניקת ה-PRP ומשתמש בציוד מתקדם להבטחת איכות הפלזמה המופקת ודיוק ההזרקה.
        """,
        
        "אולטרסאונד לתינוקות": """
בדיקת אולטרסאונד מפרקי ירך לתינוקות היא בדיקה חשובה לאבחון מוקדם של דיספלזיה התפתחותית של מפרק הירך (DDH).

מהי דיספלזיה התפתחותית של מפרק הירך (DDH)?
זהו מצב בו מפרק הירך של התינוק לא התפתח כראוי. הדבר יכול להתבטא בחוסר יציבות, תת-פריקה או פריקה מלאה של ראש עצם הירך מהאצטבולום (המכתש).

למה הבדיקה חשובה?
• אבחון מוקדם מאפשר טיפול פשוט ויעיל (לרוב באמצעות רתמה)
• ללא טיפול, ייתכנו בעיות הליכה, צליעה והתפתחות מוקדמת של דלקת מפרקים
• זיהוי וטיפול תוך 6 החודשים הראשונים מגדיל משמעותית את סיכויי ההצלחה

מתי מומלץ לבצע את הבדיקה?
• כל התינוקות: בגיל 4-6 שבועות
• תינוקות בסיכון גבוה: בדיקה ראשונה בימים הראשונים לאחר הלידה
• תינוקות בסיכון גבוה כוללים: לידת עכוז, היסטוריה משפחתית של DDH, ריבוי הריון

כיצד מתבצעת הבדיקה?
• לא פולשנית וללא כאב או קרינה
• משך הבדיקה כ-15 דקות
• לא דורשת הכנה מיוחדת
• מתבצעת על ידי ד"ר וסים המתמחה בתחום זה

ד"ר וסים מספק פענוח מיידי של הבדיקה והסבר מקיף להורים, כולל המלצות לטיפול במידת הצורך.
        """,
        
        "הערכת נכות": """
הערכות רפואיות לנכות לביטוח לאומי וחוות דעת משפטיות הן תחום התמחות חשוב של ד"ר וסים.

סוגי ההערכות:
1. חוות דעת לביטוח לאומי - להכרה בנכות ולקבלת קצבאות
2. חוות דעת לתביעות נזיקין - בתיקי תאונות דרכים, תאונות עבודה ורשלנות רפואית
3. חוות דעת למשרד הביטחון - לנפגעי צה"ל ופעולות איבה
4. הערכות לחברות ביטוח פרטיות

מה כוללת ההערכה:
• בדיקה קלינית מקיפה
• סקירת תיעוד רפואי קודם
• הערכת מגבלות תפקודיות
• קביעת דרגת נכות בהתאם לקריטריונים הרלוונטיים
• דו"ח מפורט ומקצועי

ד"ר וסים ידוע במקצועיותו הרבה ובניסוח חוות דעת בהירות ומבוססות. הדו"חות שלו מוערכים על ידי בתי משפט, הביטוח הלאומי ומוסדות רפואיים אחרים.

תהליך ההערכה:
1. פגישה ראשונית להערכה כללית
2. בדיקה מקיפה ותיעוד הממצאים
3. במקרה הצורך: הפניה לבדיקות נוספות
4. כתיבת הדו"ח המפורט
5. במקרה הצורך: עדות בבית משפט

ניתן לקבוע תור לחוות דעת דרך המרפאה. יש להגיע עם כל המסמכים הרפואיים הרלוונטיים.
        """,
        
        "טיפול בכאבי גב": """
ד"ר וסים מציע גישה מקיפה לטיפול בכאבי גב, המותאמת אישית לכל מטופל בהתאם לאבחנה ולצרכים הספציפיים.

סוגי כאבי גב שמטופלים במרפאה:
• כאבי גב תחתון (לומבגו)
• פריצות דיסק
• היצרות תעלת השדרה (ספינל סטנוזיס)
• כאבים בשורשי עצבים (רדיקולופתיה)
• דלקות מפרקים בעמוד השדרה
• נקודות טריגר שריריות

תהליך האבחון והטיפול:
1. אבחון מדויק - כולל בדיקה קלינית מקיפה וניתוח של בדיקות הדמיה
2. תכנית טיפול מותאמת אישית
3. מעקב אחר התקדמות והתאמת הטיפול בהתאם

אפשרויות טיפול:
• טיפול תרופתי - משככי כאבים, נוגדי דלקת, משחררי שרירים
• הזרקות טיפוליות - אפידורל, מפרקי פאסט, נקודות טריגר
• הפניה לפיזיותרפיה ותרגילי חיזוק ממוקדים
• טיפולי PRP לרקמות פגועות
• ייעוץ ארגונומי למניעת הישנות הכאב
• במקרים מסוימים - הפניה לשיקום או ניתוח

יתרונות הגישה של ד"ר וסים:
• טיפול שמרני לפני התערבות ניתוחית
• אבחון יסודי של מקור הכאב
• התמקדות בשיפור תפקודי ארוך טווח
• שילוב של טכניקות טיפול שונות

ד"ר וסים ידאג להסביר את מקור הכאב, אפשרויות הטיפול והפרוגנוזה בצורה ברורה ומקיפה.
        """
    }
    
    # Get the detailed information or a default message
    if topic in expanded_info:
        return expanded_info[topic].strip()
    else:
        return f"מידע מפורט על {topic} יינתן בפגישה עם ד״ר וסים. ניתן לקבוע תור לייעוץ מקיף."

def generate_post_injection_guidance(symptoms=None):
    """
    Generate detailed guidance for post-injection symptoms
    
    Args:
        symptoms (list, optional): List of reported symptoms
        
    Returns:
        str: Detailed guidance text
    """
    # Make this a shorter, more concise message to prevent WhatsApp formatting issues
    base_guidance = """
כאב לאחר הזרקה הוא תופעה נורמלית.

תופעות שכיחות:
• כאב באזור ההזרקה
• נפיחות קלה
• אדמומיות מקומית

המלצות:
• מנוחה למשך 24-48 שעות
• קירור המפרק
• משככי כאבים במידת הצורך
"""

    urgent_guidance = """
יש לפנות לרופא בהקדם אם יש:
• חום גבוה
• מפרק חם מאוד
• נפיחות חמורה
• הפרשות מהמפרק

טלפון ד״ר וסים: 0537330702
"""

    # If no specific symptoms reported, give general guidance
    if not symptoms:
        return base_guidance.strip()
    
    # Check if any urgent symptoms are reported
    urgent_symptoms = ["חום", "מפרק חם", "נפיחות", "הפרשה", "מוגלה", "זיהום", "אודם חזק"]
    has_urgent = any(symptom in urgent_symptoms for symptom in symptoms)
    
    if has_urgent:
        return f"כאב לאחר הזרקה הוא נורמלי, אך התסמינים שציינת מחייבים פנייה לרופא. אנא צור קשר עם ד\"ר וסים בטלפון: 0537330702."
    else:
        return base_guidance.strip()

def generate_response(intent, entities=None, context=None, flow=None, state=None, text=None):
    """Generate a comprehensive, natural-sounding response"""
    from custom_nlp.hebrew_nlp import HEBREW_RESPONSES
    
    # Check if this is a direct question about a treatment
    treatment_intents = ["prp_info", "steroids_info", "hyaluronic_info"]
    
    if intent in treatment_intents or (entities and 'topic' in entities):
        topic = entities.get('topic') if entities else None
        
        if not topic and intent == "prp_info":
            topic = "טיפול PRP"
        elif not topic and intent == "steroids_info":
            topic = "הזרקת סטרואידים"
        elif not topic and intent == "hyaluronic_info":
            topic = "חומצה היאלורונית"
            
        if topic:
            # Provide detailed information directly
            detailed_info = generate_expanded_information(topic, context)
            
            response = {
                "text": detailed_info,
                "options": ["תודה, מעוניין לקבוע תור", "יש לי שאלה נוספת"],
                "detected_intent": intent,
                "provided_topic": topic
            }
            
            # Update context to remember which topic was discussed
            if context is not None:
                context['last_topic'] = topic
                
            return response
    
    # Continue with regular response generation
    from custom_nlp.hebrew_nlp import HEBREW_RESPONSES
    
    # Get base response from intent
    base_response = HEBREW_RESPONSES.get(intent, HEBREW_RESPONSES['default'])
    
    # Add appropriate variation based on intent
    text = base_response.get('text', '')
    
    if intent == "greeting":
        text = add_variation(text, "greeting")
    elif intent in ["confirm", "thank_you"]:
        text = add_variation(text, "confirm")
    elif intent == "decline":
        text = add_variation(text, "understand")
    
    # Personalize the message with context
    if context:
        text = personalize_message(text, context)
    
    # Check for flow-specific responses
    if flow and state:
        # Handle special flows like appointment confirmation
        if flow == "appointment" and state == "confirmation":
            text = generate_appointment_confirmation(context)
    
    # Special handling for post-injection complaints
    if intent == "post_injection" or (entities and entities.get('is_post_injection')):
        # Get a list of reported symptoms
        symptoms = entities.get('post_injection_symptoms', []) if entities else []
        
        # Generate specific guidance
        guidance_text = generate_post_injection_guidance(symptoms)
        
        if entities and entities.get('urgent_symptoms'):
            response = {
                "text": guidance_text,
                "options": ["תודה, אתקשר לרופא", "יש לי שאלה נוספת"],
                "detected_intent": "post_injection_urgent",
                "priority": "high"
            }
        else:
            response = {
                "text": guidance_text,
                "options": ["תודה", "יש לי שאלה נוספת", "לקבוע תור מעקב"],
                "detected_intent": "post_injection"
            }
        
        return response
    
    # Check if this is a request for detailed information
    detailed_info_keywords = ["מידע נוסף", "פרטים נוספים", "להרחיב", "מידע מפורט", "הסבר"]
    topic = None
    
    if context and context.get('last_topic'):
        topic = context.get('last_topic')
    elif entities and entities.get('treatment_type'):
        topic = entities.get('treatment_type')[0] if isinstance(entities.get('treatment_type'), list) else entities.get('treatment_type')
    
    if topic and any(keyword in text for keyword in detailed_info_keywords):
        detailed_text = generate_expanded_information(topic, context)
        text = f"{add_variation('הנה מידע מפורט יותר על {topic}:', 'confirm')}\n\n{detailed_text}"
        
        # Offer fewer buttons after detailed explanation
        response = {
            "text": text,
            "options": ["תודה, מעוניין לקבוע תור", "שאלה נוספת"],
            "detected_intent": intent
        }
        
        return response
    
    # Return the full response including options
    response = {
        "text": text,
        "options": base_response.get('options', []),
        "detected_intent": intent
    }
    
    # Add flow and state information if applicable
    if flow:
        response["flow"] = flow
    if state:
        response["state"] = state
    
    return response
