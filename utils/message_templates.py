"""WhatsApp message templates in different languages"""

from venv import logger


TEMPLATES = {
    "ar": {
        "followup_check": "مرحباً {{1}}، كيف حالك اليوم بعد العلاج؟ نود الاطمئنان على صحتك.",
        "welcome_message": "مرحباً بك في عيادة د. وسيم العبرة. كيف يمكنني مساعدتك اليوم؟",
        "appointment_confirmation": "تم تأكيد موعدك يوم {{1}} الساعة {{2}}. نتطلع للقائك!",
        "post_injection_followup": "مرحباً {{1}}، كيف تشعر بعد الحقنة؟ هل هناك تحسن في حالتك؟"
    },
    "he": {
        "followup_check": "שלום {{1}}, איך אתה מרגיש היום אחרי הטיפול? אנחנו רוצים לוודא שהכל בסדר.",
        "welcome_message": "ברוך הבא למרפאה של ד״ר וסים אלעוברה. איך אני יכול לעזור לך היום?",
        "appointment_confirmation": "התור שלך אושר ליום {{1}} בשעה {{2}}. מצפים לראותך!",
        "post_injection_followup": "איך אתה מרגיש אחרי ההזרקה? האם חל שיפור במצבך?",
        "orthopedic_reminder": "תזכורת: התור שלך אצל ד״ר וסים אלעוברה (אורתופד) נקבע ליום {{1}} בשעה {{2}}. אנא אשר את הגעתך.",
        "injection_instructions": "הנחיות לאחר הזרקה: מנוחה 24-48 שעות, הימנעות ממאמץ 3-7 ימים, וקירור המפרק. אם מופיעים: חום גבוה, נפיחות חמורה, או כאב חריג - צור קשר: 0537330702."
    }
}

# Template configuration - maps template names to expected parameter counts
TEMPLATE_CONFIG = {
    "followup_status_check": {
        "he": 0,  # Hebrew version expects no parameters 
        "ar": 1   # Arabic version expects 1 parameter (name)
    },
    "appointment_confirmation": {
        "he": 2,  # Hebrew expects 2 parameters (day and time)
        "ar": 2   # Arabic expects 2 parameters (day and time)
    },
    "post_injection_followup": {
        "he": 0,  # Hebrew expects no parameters
        "ar": 1   # Arabic expects 1 parameter (name)
    }
}

def get_template_message(template_name, language="ar", params=None):
    """Get template message in the specified language with parameters filled in"""
    if language not in TEMPLATES:
        language = "ar"  # Default to Arabic
        
    if template_name not in TEMPLATES[language]:
        return None
        
    message = TEMPLATES[language][template_name]
    
    # Check if we have the right number of parameters
    expected_params = TEMPLATE_CONFIG.get(template_name, {}).get(language, 0)
    
    # Fill in parameters if provided and expected
    if params and expected_params > 0:
        # Ensure we have the right number of parameters
        if len(params) != expected_params:
            logger.warning(f"Template {template_name} in {language} expects {expected_params} params, but {len(params)} were provided")
            # Use default params if mismatch
            return message
            
        # Replace parameters in the template
        for i, value in enumerate(params):
            placeholder = f"{{{{1}}}}" if i == 0 else f"{{{{2}}}}" if i == 1 else f"{{{{3}}}}"
            message = message.replace(placeholder, str(value))
            
    return message
