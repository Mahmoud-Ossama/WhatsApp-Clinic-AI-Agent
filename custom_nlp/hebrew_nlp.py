import re
import logging
import json
import random
from datetime import datetime, timedelta
from utils.store_conversation_state import store_conversation_state, get_conversation_state
from .hebrew_nlu import detect_intent, HEBREW_INTENTS

logger = logging.getLogger(__name__)

# Default options to use when specific options aren't defined for an intent
DEFAULT_OPTIONS = {
    "greeting": ["קביעת תור", "מידע על טיפולים", "שעות פעילות", "יצירת קשר"],
    "booking": ["שעות קבלה", "מיקום המרפאה", "ביטול תור"],
    "services": ["הזרקות למפרקים", "טיפולים לילדים", "מחירים", "חזרה לתפריט"],
    "pricing": ["קביעת תור", "מידע על הזרקות", "חזרה לתפריט"],
    "doctor_info": ["השירותים שלנו", "קביעת תור", "צור קשר"],
    "injection_types": ["יתרונות וחסרונות", "מחירים", "תופעות לוואי", "קביעת תור"],
    "post_injection": ["סימני אזהרה", "צור קשר", "חזרה לתפריט"],
    "pain_complaint": ["קביעת תור דחוף", "מידע על טיפולים", "צור קשר"],
    "fallback": ["קביעת תור", "מידע על טיפולים", "צור קשר", "חזרה לתפריט"],
    "unknown": ["קביעת תור", "מידע על טיפולים", "מחירים", "צור קשר"],
    "children_services": ["אולטרסאונד לתינוקות", "בעיות הליכה", "קביעת תור"],
    "emergency": ["צור קשר עכשיו", "פנה לחדר מיון"]
}

# Hebrew intent patterns with expanded keywords and expressions
HEBREW_INTENT_PATTERNS = {
    "greeting": [
        r"\b(שלום|היי|שלומך|בוקר טוב|ערב טוב|צהריים טובים|לילה טוב|מה נשמע|מה קורה|הי|יום טוב)\b",
    ],
    "appointment_request": [
        r"\b(תור|פגישה|מועד|לקבוע|להיפגש|לתאם|הזמנת תור|אפשר תור|רוצה תור|צריך תור|מתי אפשר|זמינות)\b",
    ],
    "appointment_reschedule": [
        r"\b(לשנות תור|לדחות|להזיז|לבטל|תור אחר|מועד אחר|לא מתאים לי|אחר|שינוי)\b",
    ],
    "services": [
        r"\b(טיפול|שירות|הזרקה|הזרקות|ניתוח|טיפולים|אפשרויות|אפשר לקבל|עושים|מה אתם מציעים|מציעים|סוגי טיפולים)\b",
    ],
    "prices": [
        r"\b(מחיר|עלות|כמה עולה|תעריף|תשלום|כסף|מחירון|התעריפים|כמה זה|לשלם)\b",
    ],
    "location": [
        r"\b(איפה|מקום|כתובת|מיקום|איך מגיעים|הגעה|חניה|נמצאים|נמצא|המיקום|המרפאה|המיקום של המרפאה)\b",
    ],
    "hours": [
        r"\b(שעות|מתי|פתוח|זמנים|שעות פעילות|שעות פתיחה|ימים|פועל|פעילות|שעות פעילות|ימי עבודה|פתוחים|עובדים)\b",
    ],
    "doctor_info": [
        r"\b(רופא|דוקטור|ד״ר|מומחה|התמחות|ניסיון|השכלה|וסים|ותק|מומחיות|מוסמך)\b",
    ],
    "insurance": [
        r"\b(ביטוח|קופת חולים|מבוטח|כללית|מכבי|מאוחדת|לאומית|החזר|כיסוי|מקבלים)\b",
    ],
    "thank_you": [
        r"\b(תודה|תודה רבה|תודה לך|מעריך|מעריכה|מודה|אני מודה|בהערכה)\b",
    ],
    "confirm": [
        r"\b(כן|בסדר|מאשר|מאשרת|מסכים|מסכימה|נכון|מעולה|מצוין|טוב|אוקיי|אישור|אוקי)\b",
    ],
    "decline": [
        r"\b(לא|לא תודה|לא מעוניין|לא מעוניינת|לא רוצה|אין צורך|לא צריך|לא מסכים|לא מסכימה|טעות)\b",
    ],
    "help": [
        r"\b(עזרה|לעזור|סיוע|תמיכה|מידע|שאלה|שאלות|לשאול|מה אפשר|אפשרויות|יכול לעזור|תוכל לעזור)\b",
    ],
    "emergency": [
        r"\b(חירום|דחוף|כואב|כאב|בעיה|בעיה דחופה|מיד|מיידי|עכשיו|חייב|בדחיפות)\b",
    ],
    "goodbye": [
        r"\b(להתראות|ביי|שלום|לראות|בי|לשלום|תודה ושלום|ביי ביי|נתראה)\b",
    ],
    "doctor_bio": [
        r"\b(מי דוקטור וסים|מי ד״ר וסים|מי הרופא|רקע|ניסיון|התמחות|תחומי התמחות)\b",
    ],
    "injections": [
        r"\b(הזרקה|הזרקות|זריקה|זריקות|סטרואידים|חומצה היאלורונית|פלזמה|PRP|הילוראינית|טיפול בכאב)\b",
    ],
    "post_injection": [
        r"\b(אחרי הזרקה|לאחר הזרקה|כואב|נפיחות|אדמומיות|חום|תופעות לוואי|תופעת לוואי|כאב אחרי|תגובה להזרקה|אודם|הפרשה|מוגלה|זיהום|מפרק חם)\b",
    ],
    "pricing": [
        r"\b(עלות|מחיר|תשלום|כמה עולה|כמה זה עולה|תעריף|תעריפים)\b",
    ],
    "pediatric": [
        r"\b(ילדים|תינוק|תינוקות|ירך|בדיקת ירך|התפתחות|אולטרסאונד לתינוקות|סאונד|בדיקה לתינוק)\b",
    ],
    "disability": [
        r"\b(נכות|ביטוח לאומי|חוות דעת|משפטית|הערכה|הערכת נכות|משרד הביטחון|ועדה רפואית)\b",
    ],
    "medical_concern": [
        r"\b(דואג|מודאג|חושש|פוחד|מוטרד)\b.*?\b(תופעת לוואי|תגובה|החמרה|סיבוך)\b",
        r"\b(לא נראה לי טוב|משהו לא בסדר|משהו מוזר|מרגיש שמשהו לא נכון)\b",
        r"\b(התנפח|אדום מאוד|כאב חזק|לא יכול לזוז|חום גבוה)\b"
    ]
}

# Detailed Hebrew conversation flows
HEBREW_CONVERSATION_FLOWS = {
    "appointment": {
        "states": ["init", "day_selection", "date_selection", "time_selection", "confirmation", "completed"],
        "transitions": {
            "init": {
                "next": "day_selection",
                "response": {
                    "text": "לקביעת תור עם ד״ר וסים, אנא בחר את היום המועדף:",
                    "options": ["ראשון", "שלישי", "חמישי"]
                }
            },
            "day_selection": {
                "next": "date_selection",
                "response": {
                    "text": "אנא בחר תאריך ספציפי:",
                    "options": ["DYNAMIC_DATE_OPTIONS"]  # Will be populated dynamically
                }
            },
            "date_selection": {
                "next": "time_selection",
                "response": {
                    "text": "באיזו שעה תרצה את התור?",
                    "options": ["DYNAMIC_TIME_OPTIONS"]  # Will be populated dynamically
                }
            },
            "time_selection": {
                "next": "confirmation",
                "response": {
                    "text": "האם אתה מאשר את התור ל{day} {date} בשעה {time}?",
                    "options": ["אישור", "שינוי מועד", "ביטול"]
                }
            },
            "confirmation": {
                "next": "completed",
                "confirm_response": {
                    "text": "מצוין! התור שלך אושר ל{day} {date} בשעה {time}. שלחנו לך אישור בהודעה. נתראה בקרוב!",
                    "options": ["תודה", "לשאול שאלה", "לבטל תור"]
                },
                "change_response": {
                    "text": "אין בעיה, בוא נמצא מועד אחר.",
                    "next": "day_selection"
                },
                "cancel_response": {
                    "text": "אין בעיה, התור בוטל. האם תרצה לקבוע מועד חדש?",
                    "options": ["כן", "לא עכשיו"]
                }
            },
            "completed": {
                "next": "init",
                "response": {
                    "text": "האם אוכל לעזור לך בדבר נוסף?",
                    "options": ["מידע על טיפולים", "שעות פעילות", "צור קשר", "לא תודה"]
                }
            }
        }
    },
    "services_info": {
        "states": ["init", "service_selection", "service_details", "booking_option"],
        "transitions": {
            "init": {
                "next": "service_selection",
                "response": {
                    "text": "הנה רשימת הטיפולים שאנו מציעים:",
                    "options": ["טיפול בכאבי גב", "טיפול בכאבי צוואר", "טיפול בפריצת דיסק", "טיפול בכאבי ברכיים", "עוד טיפולים"]
                }
            },
            "service_selection": {
                "next": "service_details",
                "response": {
                    "text": "DYNAMIC_SERVICE_DETAILS",  # Will be populated based on selection
                    "options": ["מחירים", "לקבוע תור", "חזרה לתפריט"]
                }
            },
            "service_details": {
                "next": "booking_option",
                "price_response": {
                    "text": "DYNAMIC_PRICE_INFO",  # Will be populated based on service
                    "options": ["לקבוע תור", "חזרה לטיפולים", "תפריט ראשי"]
                },
                "booking_response": {
                    "text": "האם תרצה לקבוע תור לטיפול זה?",
                    "options": ["כן, לקבוע תור", "לא, תודה"]
                }
            },
            "booking_option": {
                "next": "appointment.init",  # Transition to appointment flow
                "response": {
                    "text": "מעולה, בוא נקבע תור עבורך.",
                    "flow": "appointment"  # Indicate flow change
                }
            }
        }
    },
    # Additional flows can be defined here
}

# Response templates with detailed Hebrew responses
HEBREW_RESPONSES = {
    "greeting": {
        "text": "שלום! אני העוזר הווירטואלי של ד״ר וסים. איך אוכל לעזור לך היום?",
        "options": ["קביעת תור", "מידע על טיפולים", "מחירים", "שעות פעילות"]
    },
    "appointment_request": {
        "text": "לקביעת תור אצל ד״ר וסים, אנא בקר באתר האינטרנט שלנו: https://www.wasem.co.il/\nשם תוכל לבחור את היום והשעה המתאימים לך.",
        "options": ["תודה, אבקר באתר", "שעות פעילות המרפאה", "מידע על טיפולים"]
    },
    "appointment_reschedule": {
        "text": "אין בעיה, נשמח לשנות את התור שלך. האם תוכל לציין את היום והשעה של התור הנוכחי?",
        "options": ["אין לי תור קיים", "לא זוכר את הפרטים", "קביעת תור חדש"]
    },
    "services": {
        "text": "במרפאה שלנו מציעים מגוון טיפולים, כולל טיפול בכאבי גב, צוואר, ברכיים, ופריצות דיסק. איזה טיפול מעניין אותך?",
        "options": ["טיפול בכאבי גב", "טיפול בצוואר", "פריצת דיסק", "כאבי ברכיים", "אחר"]
    },
    "prices": {
        "text": "המחירים שלנו נעים בין 250-500 ש״ח, תלוי בסוג הטיפול. יש לנו גם הסדרים עם מספר קופות חולים. איזה טיפול מעניין אותך?",
        "options": ["טיפול בגב", "הזרקות", "פיזיותרפיה", "התייעצות ראשונית"]
    },
    "location": {
        "text": "המרפאה שלנו ממוקמת ברחוב האלון 7, רעננה. יש חניה זמינה באזור. האם תרצה שנשלח לך מפה?",
        "options": ["כן, בבקשה", "איך מגיעים בתחבורה ציבורית?", "תודה, לא צריך"]
    },
    "hours": {
        "text": "שעות הפעילות שלנו הן:\nיום ראשון: 9:00-19:00\nיום שלישי: 10:00-20:00\nיום חמישי: 9:00-18:00",
        "options": ["לקבוע תור", "האם פתוח בערבי חג?", "תודה"]
    },
    "doctor_info": {
        "text": "ד״ר וסים אלעוברה הוא מומחה בכירורגיה אורטופדית, המעניק מענה מקצועי ומותאם אישית לכל מטופל. הוא מציע פתרונות מקיפים לבעיות השלד והשרירים.",
        "options": ["קביעת תור", "השירותים שלנו", "מחירים", "צור קשר"]
    },
    "insurance": {
        "text": "אנחנו עובדים עם כל קופות החולים העיקריות: כללית, מכבי, מאוחדת ולאומית. בנוסף, אנחנו מקבלים ביטוחים פרטיים רבים.",
        "options": ["פרטים על החזרים", "עלות ללא ביטוח", "קביעת תור"]
    },
    "thank_you": {
        "text": "תודה לך! אנחנו כאן כדי לעזור. האם יש משהו נוסף שאוכל לסייע בו?",
        "options": ["כן, עוד שאלה", "לא, תודה"]
    },
    "confirm": {
        "text": "מצוין! האם יש משהו נוסף שאוכל לעזור בו?",
        "options": ["כן", "לא, תודה"]
    },
    "decline": {
        "text": "אין בעיה. אם תצטרך עזרה בעתיד, אל תהסס לפנות אלינו.",
        "options": ["תודה", "יש לי שאלה אחרת"]
    },
    "help": {
        "text": "אני יכול לעזור בנושאים הבאים:",
        "options": ["קביעת תור", "מידע על טיפולים", "מחירים", "שעות פעילות", "יצירת קשר"]
    },
    "emergency": {
        "text": "אם יש לך מצב חירום רפואי, אנא התקשר למוקד החירום 101 מיד. אם זה לא חירום אבל דורש טיפול מיידי, תוכל להתקשר למרפאה בטלפון 03-1234567.",
        "options": ["להתקשר למרפאה", "קביעת תור דחוף", "תודה"]
    },
    "goodbye": {
        "text": "להתראות! שמחנו לעזור. אם תצטרך שוב את עזרתנו, אל תהסס לפנות.",
        "options": []
    },
    "doctor_bio": {
        "text": "ד״ר וסים אלעוברה הינו מומחה בכירורגיה אורטופדית, מעניק מענה מקצועי ומותאם אישית לכל מטופל, ומציע פתרונות מקיפים לבעיות השלד והשרירים. שירותיו כוללים: ייעוץ מומחה, הזרקות למפרקים (סטרואידים, חומצה היאלורונית, פלזמה), אולטראסאונד לפרקי ירך לתינוקות ואבחון מוקדם של בעיות רפואיות בתחום האורתופדית ילדים, אבחון ומעקב אחרי שברים וטראומה למערכת השלד והשרירים, הערכות נכות לביטוח לאומי, חוות דעת משפטית ולמשרד הביטחון.",
        "options": ["אילו טיפולים מוצעים", "הזרקות למפרקים", "בדיקות לילדים", "מחירים"]
    },
    "injections": {
        "text": "לפני ההחלטה על ההזרקה יש צורך שד״ר וסים יבדוק את המטופל וביחד עם המטופל ידון על אפשרויות הטיפול, יתרונות וחסרונות של כל טיפול.",
        "options": ["יתרונות וחסרונות", "מחירים", "תופעות לוואי", "קביעת תור להזרקה"]
    },
    "post_injection": {
        "text": "כאב לאחר הזרקה הוא תופעה נורמלית וצפויה, ובדרך כלל חולף תוך מספר ימים. לשיכוך הכאב ניתן להשתמש בקרח ובמשככי כאבים פשוטים. אולם, אם מופיעים סימנים כמו חום גבוה, אודם משמעותי, נפיחות חריגה, או הפרשה מהמפרק - חשוב לפנות מיד לד״ר וסים או לחדר מיון. במקרה של דאגה, ניתן ליצור קשר עם ד״ר וסים בטלפון 0537330702.",
        "options": ["סימני אזהרה", "מתי לפנות לרופא", "משככי כאבים", "צור קשר"]
    },
    "pricing": {
        "text": "עלות הייעוץ והטיפול הרפואי במרפאתנו היא 400 ש״ח. מחיר זה אינו כולל את עלות החומרים להזרקה, וכן אינו כולל הערכות נכות או חוות דעת משפטיות. לפרטים נוספים או בירור לגבי החזרים מקופות החולים, אנא צור קשר עם המרפאה.",
        "options": ["קביעת תור", "מידע על הזרקות", "חזרה לתפריט"]
    },
    "patient_inquiry": {
        "text": "תודה שפנית אלינו. כדי שנוכל לעזור לך בצורה הטובה ביותר, אנא ספר לנו:\n1. ממה אתה סובל/מתלונן?\n2. כמה זמן קיימות התלונות?\n3. האם לקחת טיפול כלשהו עד כה?",
        "options": ["קביעת תור", "מידע נוסף", "יצירת קשר"]
    },
    "prp_info": {
        "text": """
טיפול בפלזמה (PRP - Platelet-Rich Plasma) הוא טיפול חדשני המבוסס על יכולת הריפוי הטבעית של הגוף.

כיצד זה עובד:
1. נלקחת דגימת דם מהמטופל עצמו
2. הדם עובר סירכוז (סיבוב במהירות גבוהה) במכשיר מיוחד שמפריד את רכיבי הדם
3. הפלזמה העשירה בטסיות (הרכיב הריפויי) מופרדת משאר רכיבי הדם
4. הפלזמה המרוכזת מוזרקת לאזור הפגוע

הטסיות משחררות גורמי צמיחה שמעודדים ריפוי טבעי של הרקמות, מפחיתים דלקת ותומכים בבניה מחדש של רקמות פגועות.

יתרונות הטיפול:
• טיפול טבעי המבוסס על רקמות של המטופל עצמו
• סיכון נמוך לתגובות אלרגיות
• אפקט ארוך טווח (חודשים עד שנה)
• מתאים גם למטופלים שלא הגיבו לטיפולים אחרים

ד"ר וסים הוא מומחה בטכניקת ה-PRP ומשתמש בציוד מתקדם להבטחת איכות הטיפול.
    """,
    "options": ["תודה על המידע", "ברצוני לקבוע תור לטיפול", "מה העלות של טיפול PRP?"]
    },
    "post_injection_urgent": {
        "text": "אני רואה שאתה מתלונן על תסמינים שעלולים להיות חמורים לאחר הזרקה. חשוב מאוד ליצור קשר עם ד״ר וסים באופן מיידי בטלפון: 0537330702. אלו תסמינים שדורשים בדיקה מקצועית בהקדם.",
        "options": ["תודה, אתקשר עכשיו", "יש לי שאלה נוספת"]
    },
    "default": {
        "text": "שלום! אני עוזר וירטואלי של ד״ר וסים. אני יכול לעזור לך לקבוע תור, לספק מידע על טיפולים או לענות על שאלות.",
        "options": ["קביעת תור", "מידע על טיפולים", "שעות פעילות", "יצירת קשר"]
    }
}

# Service details for dynamic responses
SERVICE_DETAILS = {
    "טיפול בכאבי גב": {
        "description": "הטיפול בכאבי גב כולל אבחון מקיף של מקור הכאב ותוכנית טיפול מותאמת אישית. אנו משלבים שיטות טיפול מתקדמות כגון הזרקות, פיזיותרפיה ותרגילי חיזוק.",
        "price": "המחיר לטיפול ראשוני בכאבי גב: 400 ש״ח. טיפולי המשך: 300 ש״ח. קיימים הסדרים עם קופות חולים שונות."
    },
    "טיפול בכאבי צוואר": {
        "description": "הטיפול בכאבי צוואר מתמקד בשחרור מתחים ושיפור טווח התנועה. אנו משתמשים בטכניקות עדכניות וציוד מתקדם להקלה מיידית וארוכת טווח.",
        "price": "המחיר לטיפול בכאבי צוואר: 350 ש״ח. סדרת 5 טיפולים: 1500 ש״ח."
    },
    "טיפול בפריצת דיסק": {
        "description": "ד\"ר וסים מתמחה בטיפול שמרני בפריצות דיסק, המשלב הזרקות מדויקות בהנחיית אולטרסאונד, פיזיותרפיה ייעודית ותוכנית שיקום הדרגתית.",
        "price": "אבחון וטיפול ראשוני בפריצת דיסק: 500 ש״ח. טיפולי המשך והזרקות: 400-600 ש״ח בהתאם לסוג הטיפול."
    },
    "טיפול בכאבי ברכיים": {
        "description": "הטיפול בכאבי ברכיים מותאם לגיל המטופל ולמקור הכאב. אנו מציעים מגוון טיפולים מהזרקות ועד תרגילי חיזוק ושיקום מלא.",
        "price": "טיפול בכאבי ברכיים: 350-450 ש״ח, תלוי באבחנה וסוג הטיפול הנדרש."
    },
    "הזרקת סטרואידים": {
        "description": "הזרקת סטרואידים למפרק מפחיתה דלקת ונותנת מענה מהיר, אך לטווח קצר יחסית. ההזרקה מבוצעת בדיוק רב על ידי ד״ר וסים תוך התחשבות במצבו הרפואי של המטופל.",
        "price": "עלות הייעוץ והטיפול: 400 ש״ח. מחיר החומר להזרקה הוא בתשלום נוסף. יש אפשרות להחזר מקופות החולים בהתאם לסוג הביטוח."
    },
    "הזרקת חומצה היאלורונית": {
        "description": "הזרקת חומצה היאלורונית משמשת כג'ל בברך ומסייעת בתנועתיות המפרק. ההשפעה נמשכת כחצי שנה עד שנה לפי החברה המייצרת. הטיפול מתאים במיוחד למפרקים עם שחיקה.",
        "price": "עלות הייעוץ והטיפול: 400 ש״ח. מחיר החומצה ההיאלורונית הוא בתשלום נוסף ותלוי בסוג החומר. קיימים מספר סוגים בהתאם לצורך."
    },
    "הזרקת פלזמה (PRP)": {
        "description": "הזרקת פלזמה עשירה בטסיות (PRP) היא טיפול חדשני המבוסס על יכולת הריפוי הטבעית של הגוף. ד״ר וסים לוקח דם מהמטופל, מפריד את הטסיות העשירות באמצעות ציוד ייעודי, ומזריק אותן למפרק לעידוד תהליכי ריפוי.",
        "price": "עלות הייעוץ והטיפול: 400 ש״ח. עלות הכנת ה-PRP משתנה ומוסברת בפגישה עם הרופא."
    },
    "אולטרסאונד לתינוקות": {
        "description": "בדיקת אולטרסאונד למפרקי ירך בתינוקות מסייעת באבחון מוקדם של בעיות התפתחותיות. אבחון מוקדם חיוני למניעת סיבוכים עתידיים ולטיפול יעיל. הבדיקה מתבצעת על ידי ד״ר וסים באופן עדין ובטוח.",
        "price": "עלות הבדיקה: 400 ש״ח."
    }
}

def detect_hebrew_intent(text):
    """
    Enhanced detection of intent from Hebrew text using both pattern matching and NLU.
    
    Args:
        text (str): User's message in Hebrew
        
    Returns:
        dict: Intent details with name and confidence
    """
    # First try the advanced NLU approach
    detection_result = detect_intent(text)
    intent = detection_result['intent']
    confidence = detection_result['confidence']
    
    # If NLU gave us a high-confidence result, use it
    if confidence >= 0.4 or intent != "unknown":
        # Extract entities using both methods and combine them
        pattern_entities = extract_hebrew_entities(text.lower())
        nlu_entities = detection_result['entities']
        
        # Merge entities, giving preference to pattern-based extraction for specific fields
        combined_entities = {**nlu_entities, **pattern_entities}
        
        logger.debug(f"Hebrew intent via NLU: {intent} with confidence {confidence}")
        
        return {
            "intent": intent,
            "confidence": confidence,
            "entities": combined_entities
        }
    
    # Fall back to pattern-based approach
    # Default values
    best_intent = "default"
    best_confidence = 0.0
    
    # Normalize text for better matching (remove extra spaces, lowercase)
    normalized_text = re.sub(r'\s+', ' ', text.lower().strip())
    
    # Check each intent pattern
    for intent_name, patterns in HEBREW_INTENT_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, normalized_text, re.IGNORECASE)
            if matches:
                # Calculate confidence based on match length and count
                match_ratio = sum(len(m) for m in matches) / len(normalized_text) if normalized_text else 0
                match_count = len(matches)
                confidence = (match_ratio * 0.7) + (match_count * 0.1)
                
                if confidence > best_confidence:
                    best_intent = intent_name
                    best_confidence = min(confidence, 0.95)  # Cap at 0.95
    
    logger.debug(f"Hebrew intent via patterns: {best_intent} with confidence {best_confidence}")
    
    return {
        "intent": best_intent,
        "confidence": best_confidence,
        "entities": extract_hebrew_entities(normalized_text)
    }

def extract_hebrew_entities(text):
    """
    Extract relevant entities from Hebrew text
    
    Args:
        text (str): The Hebrew text to analyze
        
    Returns:
        dict: Dictionary of extracted entities
    """
    entities = {}
    
    # Body parts - joints
    joint_patterns = [
        r"\b(ברך|ברכיים|כתף|כתפיים|מרפק|מרפקים|קרסול|קרסוליים|גב|צוואר|מותן|מותניים|ירך|ירכיים)\b"
    ]
    
    for pattern in joint_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            entities.setdefault('joint', []).append(match.group(0))
    
    # Injection types
    injection_patterns = [
        r"\b(סטרואיד|סטרואידים|קורטיזון|היאלורונית|חומצה היאלורונית|פלזמה|PRP)\b"
    ]
    
    for pattern in injection_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            entities.setdefault('injection_type', []).append(match.group(0))
    
    # Post-injection detection
    if any(term in text.lower() for term in ["אחרי הזרקה", "לאחר הזרקה", "קיבלתי הזרקה"]):
        entities['is_post_injection'] = True
    
    # Symptom detection for post-injection
    post_injection_symptoms = [
        "כאב", "נפיחות", "אודם", "חום", "דלקת", "הגבלה", "אי נוחות",
        "מוגלה", "הפרשה", "זיהום", "אדמומיות", "חום גבוה", "מפרק חם"
    ]
    
    found_symptoms = []
    for symptom in post_injection_symptoms:
        if symptom in text.lower():
            found_symptoms.append(symptom)
    
    if found_symptoms:
        entities['symptoms'] = found_symptoms
    
    # Identify urgent symptoms
    urgent_symptoms = ["חום גבוה", "מפרק חם", "נפיחות גדולה", "הפרשה", "מוגלה"]
    if any(symptom in text.lower() for symptom in urgent_symptoms):
        entities['urgent_symptoms'] = True
    
    return entities

def generate_dynamic_options(flow_state, context):
    """Generate dynamic response options based on flow state and context"""
    if flow_state == "appointment.day_selection":
        # Generate date options for the selected day
        day = context.get('selected_day', 'ראשון')
        today = datetime.now()
        options = []
        
        # Map Hebrew day name to weekday number (0 = Monday in Python)
        day_mapping = {'ראשון': 6, 'שני': 0, 'שלישי': 1, 'רביעי': 2, 'חמישי': 3, 'שישי': 4, 'שבת': 5}
        target_weekday = day_mapping.get(day, 6)  # Default to Sunday
        
        # Find the next 4 occurrences of the target weekday
        current_date = today
        while len(options) < 4:
            if current_date.weekday() == target_weekday:
                # Format: "יום ראשון, 01/04"
                date_str = current_date.strftime("%d/%m")
                options.append(f"{day}, {date_str}")
            current_date += timedelta(days=1)
        
        return options
        
    elif flow_state == "appointment.time_selection":
        # Generate time slots based on the selected day
        day = context.get('selected_day', 'ראשון')
        
        # Different time slots per day
        time_slots = {
            'ראשון': ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00", "18:00"],
            'שלישי': ["10:00", "11:00", "12:00", "13:00", "15:00", "16:00", "17:00", "18:00", "19:00"],
            'חמישי': ["09:00", "10:00", "11:30", "12:30", "14:00", "15:00", "16:00", "17:00"]
        }
        
        return time_slots.get(day, ["09:00", "11:00", "13:00", "15:00", "17:00"])
    
    # Default options if no specific logic applies
    return ["אפשרות 1", "אפשרות 2", "אפשרות 3"]

def get_service_details(service_name):
    """Get detailed information about a specific service"""
    service_info = SERVICE_DETAILS.get(service_name, {
        "description": "מידע מפורט על טיפול זה לא זמין כרגע. נשמח לספק מידע בשיחה עם הרופא.",
        "price": "המחיר משתנה בהתאם לסוג הטיפול הספציפי. לפרטים נוספים, אנא צור קשר עם המרפאה."
    })
    
    return service_info

def process_hebrew_text(text, sender_id=None):
    """
    Process Hebrew text to extract intent and entities
    
    Args:
        text (str): Text to process
        sender_id (str, optional): User identifier for context
        
    Returns:
        dict: Dictionary with detected intent and entities
    """
    try:
        # First check for exact matches to common phrases
        text_lower = text.lower().strip()
        
        # Direct mapping for common phrases
        if any(hours_term in text_lower for hours_term in ["שעות", "שעות פעילות", "פתוח", "פתיחה"]):
            return {
                "detected_intent": "hours",
                "confidence": 1.0,
                "text": text,
                "entities": {}
            }
            
        if any(term in text_lower for term in ["מחיר", "עלות", "תשלום", "כמה עולה", "עולה"]):
            return {
                "detected_intent": "pricing",
                "confidence": 0.9,
                "text": text,
                "response_text": "עלות הטיפול היעוץ והטיפול הרפואי הוא 400 ש״ח.\nהמחיר אינו כולל עלות חומרים להזרקה או הערכות נכות וחוות דעת משפטיות.",
                "entities": {}
            }
            
        if any(term in text_lower for term in ["תור", "לקבוע", "הזמנה", "להזמין"]):
            return {
                "detected_intent": "booking",
                "confidence": 0.95,
                "text": text,
                "entities": {}
            }

        # Continue with standard intent detection
        intent_info = detect_hebrew_intent(text)
        
        return {
            "detected_intent": intent_info['intent'],
            "confidence": intent_info['confidence'],
            "text": text,
            "entities": intent_info.get('entities', {})
        }
    except Exception as e:
        logger.error(f"Error in process_hebrew_text: {str(e)}", exc_info=True)
        # Return a fallback intent instead of None
        return {
            "detected_intent": "fallback",
            "confidence": 0.0,
            "text": text,
            "entities": {}
        }

def process_patient_complaint(text):
    """Process initial patient complaints and generate appropriate response"""
    response = {
        "text": "אנחנו כאן לרשותך ונעזור לך להחלים ולהתגבר על הכאב שלך. ד״ר וסים מתמחה בטיפול בבעיות כאלה ויוכל לתת לך טיפול מותאם אישית. האם תרצה לקבוע תור?",
        "options": ["כן, אשמח לקבוע תור", "יש לי שאלות נוספות", "מה עלות הטיפול?"],
        "detected_intent": "patient_inquiry"
    }
    
    return response
