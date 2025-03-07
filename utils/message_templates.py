# Template IDs from WhatsApp Business API
TEMPLATE_IDS = {
    'followup_check': 'followup_status_check',  # You need to create this template in WhatsApp Business Manager
    'injection_confirmation': 'injection_confirmation'
}

def get_template_message(template_name, language, params=None):
    """Get template message based on language"""
    templates = {
        'followup_check': {
            'name': TEMPLATE_IDS['followup_check'],
            'language': 'ar' if language == 'arab' else 'he',
            'components': [
                {
                    'type': 'body',
                    'parameters': [
                        {'type': 'text', 'text': params['patient_name'] if params else ''}
                    ]
                }
            ]
        }
    }
    return templates.get(template_name)
