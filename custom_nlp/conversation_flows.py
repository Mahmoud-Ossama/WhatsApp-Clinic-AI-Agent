"""
Structured conversation flows for Dr. Wasim's orthopedic clinic.
These flows define the conversation paths for different user scenarios.
"""
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Reusable transitions and responses that can be used across flows
COMMON_TRANSITIONS = {
    "back_to_main": {
        "text": "האם אוכל לעזור לך בנושא אחר?",
        "options": ["קביעת תור", "מידע על טיפולים", "שעות הקליניקה", "יצירת קשר"]
    },
    "confirm_exit": {
        "text": "האם אתה בטוח שברצונך לסיים את השיחה?",
        "options": ["כן", "לא, ברצוני להמשיך"]
    },
    "thank_you": {
        "text": "תודה שפנית אלינו. נשמח לעזור לך בכל שאלה נוספת!",
        "options": ["חזרה לתפריט הראשי", "סיום שיחה"]
    }
}

# =====================
# 1. WELCOME FLOW
# =====================
WELCOME_FLOW = {
    "name": "welcome",
    "initial_state": "greeting",
    "states": {
        "greeting": {
            "message": {
                "text": "שלום! אני העוזר הווירטואלי של מרפאת ד״ר וסים אלעוברה, מומחה בכירורגיה אורטופדית. במה אוכל לעזור לך היום?",
                "options": ["קביעת תור", "מידע על טיפולים", "הזרקות מפרקים", "בדיקות לילדים", "אודות ד״ר וסים"]
            },
            "transitions": {
                "קביעת תור": "FLOW:booking.init",
                "מידע על טיפולים": "FLOW:catalog.services",
                "הזרקות מפרקים": "FLOW:catalog.injections",
                "בדיקות לילדים": "FLOW:catalog.pediatric",
                "אודות ד״ר וסים": "doctor_bio",
                "default": "FLOW:catalog.services"
            }
        },
        "doctor_bio": {
            "message": {
                "text": "ד״ר וסים אלעוברה הינו מומחה בכירורגיה אורטופדית, מעניק מענה מקצועי ומותאם אישית לכל מטופל, ומציע פתרונות מקיפים לבעיות השלד והשרירים. שירותיו כוללים: ייעוץ מומחה, הזרקות למפרקים (סטרואידים, חומצה היאלורונית, פלזמה), אולטראסאונד לפרקי ירך לתינוקות ואבחון מוקדם של בעיות רפואיות בתחום האורתופדית ילדים, אבחון ומעקב אחרי שברים וטראומה למערכת השלד והשרירים, הערכות נכות לביטוח לאומי, חוות דעת משפטית ולמשרד הביטחון.",
                "options": ["מידע על טיפולים", "לקבוע תור", "חזרה לתפריט"]
            },
            "transitions": {
                "מידע על טיפולים": "FLOW:catalog.services",
                "לקבוע תור": "FLOW:booking.init",
                "חזרה לתפריט": "greeting",
                "default": "greeting"
            }
        }
    }
}

# =====================
# 2. CATALOG FLOW
# =====================
CATALOG_FLOW = {
    "name": "catalog",
    "initial_state": "services",
    "states": {
        # Main services overview
        "services": {
            "message": {
                "text": "ד״ר וסים מציע מגוון טיפולים במרפאה, כולל:\n\n- ייעוץ מומחה\n- הזרקות למפרקים (סטרואידים, חומצה היאלורונית, פלזמה)\n- אולטראסאונד למפרקי ירך לתינוקות\n- אבחון ומעקב אחרי שברים וטראומה למערכת השלד והשרירים\n- הערכות נכות לביטוח לאומי, חוות דעת משפטית ולמשרד הביטחון\n\nמעוניין לקבל מידע נוסף על אחד מהשירותים?",
                "options": ["הזרקות מפרקים", "טיפול בכאבי גב", "בדיקות לילדים", "הערכות נכות", "מחירים", "לקביעת תור"]
            },
            "transitions": {
                "הזרקות מפרקים": "injections",
                "טיפול בכאבי גב": "back_pain",
                "בדיקות לילדים": "pediatric",
                "הערכות נכות": "disability",
                "מחירים": "pricing",
                "לקביעת תור": "FLOW:booking.init",
                "default": "injections"
            }
        },
        
        # Injections information
        "injections": {
            "message": {
                "text": "ד״ר וסים מבצע מספר סוגי הזרקות למפרקים. לפני ההחלטה על סוג ההזרקה, ד״ר וסים יבדוק אותך ויתייעץ איתך על אפשרויות הטיפול, היתרונות והחסרונות של כל טיפול. על איזה סוג הזרקה תרצה לדעת יותר?",
                "options": ["הזרקת סטרואידים", "חומצה היאלורונית", "טיפול בפלזמה (PRP)", "מידע כללי"]
            },
            "transitions": {
                "הזרקת סטרואידים": "steroids",
                "חומצה היאלורונית": "hyaluronic",
                "טיפול בפלזמה (PRP)": "prp",
                "מידע כללי": "general_injections",
                "default": "general_injections",
                "חזרה": "services"
            }
        },
        
        # Steroids injection details
        "steroids": {
            "message": {
                "text": """
הזרקת סטרואידים: מורידה דלקת ונותנת מענה מהיר לכאב, אך בעיקר לטווח קצר. התרופה יחסית זולה כספית. 

החיסרון הוא שהיא עוזרת לתקופה קצרה, ויש צורך במעקב צמוד אחר רמת הסוכר ולחץ הדם, במיוחד אצל מטופלים עם רקע של סכרת ויתר לחץ דם.

הטיפול מתאים במיוחד למצבים של דלקת חריפה ויכול לתת הקלה משמעותית כשמבוצע בידי מומחה כמו ד״ר וסים.
""",
                "options": ["לקבוע תור להזרקה", "השוואה בין סוגי הזרקות", "מחיר הטיפול", "חזרה לתפריט"]
            },
            "transitions": {
                "לקבוע תור להזרקה": "FLOW:booking.init",
                "השוואה בין סוגי הזרקות": "compare_injections",
                "מחיר הטיפול": "pricing",
                "חזרה לתפריט": "injections",
                "default": "injections"
            }
        },
        
        # Hyaluronic acid injection details
        "hyaluronic": {
            "message": {
                "text": """
החומצה ההיאלורונית משמשת כמו ג'ל בברך ומטרתה לעזור בתנועתיות המפרק. ישנם מספר סוגים שונים, ולפי החברה המייצרת הג'ל אמור לתת הקלה ולעזור למשך כחצי שנה עד שנה.

טיפול זה מתאים במיוחד למטופלים עם שחיקת סחוס (אוסטאוארטריטיס) שאינם מגיבים מספיק טוב לטיפולים תרופתיים רגילים.

ד״ר וסים יתאים את סוג החומצה ההיאלורונית המדויק למצבך הרפואי ולמפרק המטופל.
""",
                "options": ["לקבוע תור להזרקה", "השוואה בין סוגי הזרקות", "מחיר הטיפול", "חזרה לתפריט"]
            },
            "transitions": {
                "לקבוע תור להזרקה": "FLOW:booking.init",
                "השוואה בין סוגי הזרקות": "compare_injections",
                "מחיר הטיפול": "pricing",
                "חזרה לתפריט": "injections",
                "default": "injections"
            }
        },
        
        # PRP injection details
        "prp": {
            "message": {
                "text": """
טיפול בפלזמה (PRP) הוא טיפול חדשני ומהפכני המבוסס על טיפול טבעי ויכולת הריפוי העצמית של הגוף. במרפאה, ד״ר וסים ייקח דם מיד המטופל, ובאמצעות ציוד ייעודי יבצע הפרדה של התאים כך שיופרדו הטסיות העשירות משאר מרכיבי הדם. 

הטסיות העשירות עוזרות ומעודדות ריפוי במפרק דרך שחרור גורמי צמיחה טבעיים שמזרזים את תהליכי הריפוי, מפחיתים דלקת ומסייעים בבניה מחדש של רקמות פגועות.

טיפול זה מתאים במיוחד למטופלים שמעוניינים בגישה טבעית יותר, ויכול להיות יעיל גם במקרים שלא הגיבו לטיפולים אחרים.
""",
                "options": ["לקבוע תור להזרקה", "השוואה בין סוגי הזרקות", "מחיר הטיפול", "חזרה לתפריט"]
            },
            "transitions": {
                "לקבוע תור להזרקה": "FLOW:booking.init",
                "השוואה בין סוגי הזרקות": "compare_injections",
                "מחיר הטיפול": "pricing",
                "חזרה לתפריט": "injections",
                "default": "injections"
            }
        },
        
        # General injection information
        "general_injections": {
            "message": {
                "text": "חשוב מאוד להבין שההחלטה על סוג הטיפול היא בהתייעצות עם ד״ר וסים, לאחר בדיקה גופנית ומעבר על הדמיה (צילום רנטגן, MRI וכדומה), ובתיאום עם המטופל על הטיפול המתאים ביותר לו.",
                "options": ["השוואה בין סוגי הזרקות", "מחיר הטיפול", "לקבוע תור", "חזרה לתפריט"]
            },
            "transitions": {
                "השוואה בין סוגי הזרקות": "compare_injections",
                "מחיר הטיפול": "pricing",
                "לקבוע תור": "FLOW:booking.init",
                "חזרה לתפריט": "injections",
                "default": "injections"
            }
        },
        
        # Comparison between injection types
        "compare_injections": {
            "message": {
                "text": "השוואה בין סוגי ההזרקות:\n\n1. סטרואידים: מהיר, זול, לטווח קצר. דורש מעקב אחר סוכר ולחץ דם.\n\n2. חומצה היאלורונית: משפר תנועתיות, השפעה ל-6-12 חודשים, עלות בינונית.\n\n3. פלזמה (PRP): טבעי, מעודד ריפוי, חדשני, עלות גבוהה יותר.\n\nההחלטה הסופית תלויה במצבך הרפואי ובהמלצת הרופא.",
                "options": ["לקבוע תור לייעוץ", "מחיר הטיפול", "חזרה לסוגי הזרקות"]
            },
            "transitions": {
                "לקבוע תור לייעוץ": "FLOW:booking.init",
                "מחיר הטיפול": "pricing",
                "חזרה לסוגי הזרקות": "injections",
                "default": "injections"
            }
        },
        
        # Back pain treatment
        "back_pain": {
            "message": {
                "text": "ד״ר וסים מתמחה בטיפול בכאבי גב מסוגים שונים. הטיפול כולל אבחון מדויק של מקור הכאב ובניית תכנית טיפול מותאמת אישית, שעשויה לכלול: הזרקות, המלצות לפיזיותרפיה, תרגילי חיזוק, והתאמת טיפול תרופתי.",
                "options": ["לקבוע תור", "מחיר הטיפול", "מידע על הזרקות", "חזרה לתפריט"]
            },
            "transitions": {
                "לקבוע תור": "FLOW:booking.init",
                "מחיר הטיפול": "pricing",
                "מידע על הזרקות": "injections",
                "חזרה לתפריט": "services",
                "default": "services"
            }
        },
        
        # Pediatric services
        "pediatric": {
            "message": {
                "text": "ד״ר וסים מתמחה גם באורתופדיית ילדים, כולל אולטראסאונד למפרקי ירך בתינוקות ואבחון מוקדם של בעיות רפואיות בתחום האורתופדיה. האבחון המוקדם חיוני למניעת בעיות התפתחותיות עתידיות ומאפשר טיפול יעיל.",
                "options": ["מידע על אולטרסאונד לתינוקות", "לקבוע תור לילד", "מחיר הבדיקה", "חזרה לתפריט"]
            },
            "transitions": {
                "מידע על אולטרסאונד לתינוקות": "ultrasound_info",
                "לקבוע תור לילד": "FLOW:booking.init",
                "מחיר הבדיקה": "pricing",
                "חזרה לתפריט": "services",
                "default": "services"
            }
        },
        
        # Ultrasound for infants info
        "ultrasound_info": {
            "message": {
                "text": "אולטראסאונד למפרקי ירך בתינוקות הוא בדיקה חשובה לאבחון מוקדם של בעיות התפתחותיות במפרק הירך. הבדיקה מומלצת לתינוקות בגילאי שבועות עד חודשים ספורים ואינה כרוכה בכאב או אי נוחות. זיהוי מוקדם מאפשר טיפול פשוט ויעיל.",
                "options": ["לקבוע תור לבדיקה", "מחיר הבדיקה", "חזרה לתפריט"]
            },
            "transitions": {
                "לקבוע תור לבדיקה": "FLOW:booking.init",
                "מחיר הבדיקה": "pricing",
                "חזרה לתפריט": "pediatric",
                "default": "pediatric"
            }
        },
        
        # Disability assessment services
        "disability": {
            "message": {
                "text": "ד״ר וסים מבצע הערכות נכות לביטוח לאומי, חוות דעת משפטיות וחוות דעת למשרד הביטחון. שירותים אלה דורשים הכנה מראש וכוללים בדיקה מקיפה, עיון במסמכים רפואיים והכנת דו\"ח מפורט.",
                "options": ["לקבוע תור להערכה", "מחיר השירות", "חזרה לתפריט"]
            },
            "transitions": {
                "לקבוע תור להערכה": "FLOW:booking.init",
                "מחיר השירות": "pricing",
                "חזרה לתפריט": "services",
                "default": "services"
            }
        },
        
        # Pricing information
        "pricing": {
            "message": {
                "text": """
עלות הייעוץ והטיפול הרפואי אצל ד״ר וסים היא 400 ש״ח. 

מחיר זה כולל:
• בדיקה מקיפה על ידי מומחה
• אבחון והערכה מדויקת של מצבך
• קביעת תכנית טיפול אישית
• הסבר מפורט על מצבך הרפואי ואפשרויות הטיפול

מחיר זה אינו כולל:
• עלות חומרים להזרקה (במקרה של הזרקות למפרקים)
• הערכות נכות וחוות דעת משפטיות (מתומחרות בנפרד)
• בדיקות הדמיה נוספות אם יידרשו

לגבי החזרים מקופות חולים - ד״ר וסים עובד עם כל קופות החולים העיקריות, אך ההחזר תלוי בסוג הביטוח שלך. המרפאה תספק את כל המסמכים הדרושים לקבלת החזר.

למידע נוסף על מחירים ספציפיים, אנא צור קשר עם המרפאה.
""",
                "options": ["לקבוע תור", "מידע על החזרים מקופ\"ח", "חזרה לתפריט"]
            },
            "transitions": {
                "לקבוע תור": "FLOW:booking.init",
                "מידע על החזרים מקופ\"ח": "insurance",
                "חזרה לתפריט": "services",
                "default": "services"
            }
        },
        
        # Insurance and refunds information
        "insurance": {
            "message": {
                "text": "ד״ר וסים עובד עם כל קופות החולים העיקריות, אך ההחזר או הכיסוי תלוי בסוג הביטוח האישי שלך. מומלץ לבדוק מול קופת החולים שלך מראש. המרפאה תספק את כל המסמכים הנדרשים לקבלת החזר במידת האפשר.",
                "options": ["לקבוע תור", "חזרה לתפריט"]
            },
            "transitions": {
                "לקבוע תור": "FLOW:booking.init",
                "חזרה לתפריט": "pricing",
                "default": "pricing"
            }
        }
    }
}

# =====================
# 3. BOOKING FLOW
# =====================
BOOKING_FLOW = {
    "name": "booking",
    "initial_state": "init",
    "states": {
        # Initial booking screen
        "init": {
            "message": {
                "text": "לקביעת תור אצל ד״ר וסים, אנא בקר באתר האינטרנט שלנו:\nhttps://www.wasem.co.il/\n\nבאתר תוכל לראות את כל התורים הזמינים ולבחור את המועד המתאים לך ביותר.",
                "options": ["שאלה לגבי הטיפולים", "חזרה לתפריט הראשי"]
            },
            "transitions": {
                "שאלה לגבי הטיפולים": "FLOW:catalog.services",
                "חזרה לתפריט הראשי": "FLOW:welcome.greeting",
                "default": "website_confirmation"
            }
        },
        
        # Confirmation after user indicates they will visit the website
        "website_confirmation": {
            "message": {
                "text": "מצוין! באתר https://www.wasem.co.il/ תוכל לבחור את היום והשעה המתאימים לך, וכן לציין את סוג הטיפול המבוקש.\n\nהאם אוכל לעזור לך במשהו נוסף?",
                "options": ["מידע על טיפולים", "שעות פעילות", "מחירים", "חזרה לתפריט"]
            },
            "transitions": {
                "מידע על טיפולים": "FLOW:catalog.services",
                "שעות פעילות": "hours_info",
                "מחירים": "FLOW:catalog.pricing",
                "חזרה לתפריט": "FLOW:welcome.greeting",
                "default": "FLOW:welcome.greeting"
            }
        },
        
        # Hours information
        "hours_info": {
            "message": {
                "text": "שעות קבלה של ד״ר וסים:\nיום ראשון: 9:00-19:00\nיום שלישי: 10:00-20:00\nיום חמישי: 9:00-18:00\n\nלקביעת תור, אנא בקר באתר: https://www.wasem.co.il/",
                "options": ["מידע על טיפולים", "חזרה לתפריט"]
            },
            "transitions": {
                "מידע על טיפולים": "FLOW:catalog.services", 
                "חזרה לתפריט": "FLOW:welcome.greeting",
                "default": "FLOW:welcome.greeting"
            }
        }
    }
}

# =====================
# 4. INJECTED PATIENT FLOW
# =====================
INJECTED_PATIENT_FLOW = {
    "name": "injected_patient",
    "initial_state": "check_status",
    "states": {
        # Initial status check
        "check_status": {
            "message": {
                "text": "שלום! איך אתה מרגיש אחרי ההזרקה? האם חל שיפור במצבך?",
                "options": ["יש שיפור משמעותי", "יש שיפור קל", "אין שינוי", "יש החמרה"]
            },
            "transitions": {
                "יש שיפור משמעותי": "significant_improvement",
                "יש שיפור קל": "mild_improvement",
                "אין שינוי": "no_change",
                "יש החמרה": "worsening",
                "default": "misc_symptoms"
            },
            "save_context": "improvement_status"
        },
        
        # Significant improvement path
        "significant_improvement": {
            "message": {
                "text": "אני שמח לשמוע שחל שיפור משמעותי! זו תגובה טובה מאוד לטיפול. האם אתה חווה תופעות לוואי כלשהן?",
                "options": ["לא, הכל בסדר", "יש לי תופעות לוואי קלות", "יש לי שאלה נוספת"]
            },
            "transitions": {
                "לא, הכל בסדר": "followup_recommendation",
                "יש לי תופעות לוואי קלות": "side_effects",
                "יש לי שאלה נוספת": "misc_symptoms",
                "default": "followup_recommendation"
            }
        },
        
        # Mild improvement path
        "mild_improvement": {
            "message": {
                "text": "שיפור קל הוא גם סימן טוב. לעתים לוקח קצת זמן עד שמרגישים את מלוא ההשפעה של הטיפול. האם יש לך כאבים או אי נוחות?",
                "options": ["יש לי עדיין קצת כאבים", "המפרק נפוח או אדום", "אני מרגיש בסדר", "יש לי שאלות"]
            },
            "transitions": {
                "יש לי עדיין קצת כאבים": "pain_management",
                "המפרק נפוח או אדום": "side_effects",
                "אני מרגיש בסדר": "followup_recommendation",
                "יש לי שאלות": "misc_symptoms",
                "default": "followup_recommendation"
            }
        },
        
        # No change path
        "no_change": {
            "message": {
                "text": "לפעמים לוקח מספר ימים עד שמתחילים להרגיש את השיפור מההזרקה. האם חולפו כבר יותר מ-3 ימים מאז ההזרקה?",
                "options": ["כן, יותר מ-3 ימים", "לא, פחות מ-3 ימים", "יש לי גם תופעות לוואי"]
            },
            "transitions": {
                "כן, יותר מ-3 ימים": "recommend_contact",
                "לא, פחות מ-3 ימים": "wait_longer",
                "יש לי גם תופעות לוואי": "side_effects",
                "default": "recommend_contact"
            }
        },
        
        # Worsening condition path
        "worsening": {
            "message": {
                "text": "אני מצטער לשמוע שיש החמרה. האם יש לך אחד מהתסמינים הבאים: חום גבוה, אדמומיות חזקה, נפיחות חריגה, הפרשות מהמפרק, או כאב חמור שלא מגיב למשככי כאבים?",
                "options": ["כן, יש לי אחד או יותר מהתסמינים", "לא, אך הכאב חזק יותר מקודם", "לא בטוח"]
            },
            "transitions": {
                "כן, יש לי אחד או יותר מהתסמינים": "urgent_contact",
                "לא, אך הכאב חזק יותר מקודם": "recommend_contact",
                "לא בטוח": "recommend_contact",
                "default": "recommend_contact"
            }
        },
        
        # Urgent contact needed
        "urgent_contact": {
            "message": {
                "text": "תסמינים אלו עלולים להצביע על זיהום או תגובה חריגה ומצריכים פנייה דחופה לרופא. אנא צור קשר עם ד״ר וסים בהקדם בטלפון 0537330702 או פנה למיון הקרוב אם המצב חמור. חשוב לציין שיש לך חום גבוה, נפיחות ניכרת, אדמומיות או הפרשות מהמפרק.",
                "options": ["תודה, אתקשר כעת", "אני צריך מידע נוסף"]
            },
            "transitions": {
                "תודה, אתקשר כעת": "end_conversation",
                "אני צריך מידע נוסף": "provide_contact_info",
                "default": "provide_contact_info"
            },
            "priority": "high"
        },
        
        # Provide contact information
        "provide_contact_info": {
            "message": {
                "text": "מספר הטלפון של ד\"ר וסים: 0537330702\nשעות המרפאה: ראשון, שלישי וחמישי.\nבמקרה של חירום מחוץ לשעות המרפאה, יש לפנות למיון או למוקד רפואה דחופה.",
                "options": ["תודה", "לקבוע תור מעקב"]
            },
            "transitions": {
                "תודה": "end_conversation",
                "לקבוע תור מעקב": "FLOW:booking.init",
                "default": "end_conversation"
            }
        },
        
        # Side effects management
        "side_effects": {
            "message": {
                "text": "כאב לאחר הזרקה הוא נורמלי וצפוי. תופעות לוואי מסוימות כמו אי נוחות קלה, נפיחות מינורית או אדמומיות קלה הן נורמליות בימים הראשונים שלאחר ההזרקה.\n\nאך חשוב לשים לב לסימנים מדאיגים כמו:\n- חום סיסטמי גבוה\n- מפרק חם למגע\n- נפיחות ניכרת\n- הפרשות מהמפרק\n\nהאם אתה חווה אחד מהתסמינים האלה?",
                "options": ["לא, רק תופעות קלות", "כן, יש לי אחד מהתסמינים החמורים", "לא בטוח"]
            },
            "transitions": {
                "לא, רק תופעות קלות": "normal_side_effects",
                "כן, יש לי אחד מהתסמינים החמורים": "urgent_contact",
                "לא בטוח": "recommend_contact",
                "default": "normal_side_effects"
            }
        },
        
        # Normal side effects guidance
        "normal_side_effects": {
            "message": {
                "text": "תופעות לוואי קלות הן חלק נורמלי מתהליך ההחלמה. המלצות להקלה: מנוחה, קירור המפרק (20 דקות כל שעתיים), הימנעות ממאמץ, והרמת הגפה במידת האפשר. אם התופעות נמשכות יותר מ-48 שעות או מחמירות, צור קשר עם המרפאה.",
                "options": ["הבנתי, תודה", "יש לי שאלה נוספת", "לקבוע תור מעקב"]
            },
            "transitions": {
                "הבנתי, תודה": "followup_recommendation",
                "יש לי שאלה נוספת": "misc_symptoms",
                "לקבוע תור מעקב": "FLOW:booking.init",
                "default": "followup_recommendation"
            }
        },
        
        # Pain management advice
        "pain_management": {
            "message": {
                "text": "כאב לאחר הזרקה הוא תופעה נורמלית וצפויה, ויכול להימשך עד 48 שעות. ניתן להקל על הכאב באמצעות:\n\n- מנוחה והימנעות ממאמץ\n- קירור המפרק (20 דקות כל שעתיים)\n- משככי כאבים כמו אקמול או נורופן על פי המלצת הרופא\n\nאם הכאב חמור מאוד, נמשך יותר מ-3 ימים, או מלווה בחום/אדמומיות/נפיחות חריגה - יש ליצור קשר עם ד\"ר וסים בטלפון: 0537330702",
                "options": ["תודה, אנסה את ההמלצות", "הכאב חמור מאוד", "לקבוע תור מעקב"]
            },
            "transitions": {
                "תודה, אנסה את ההמלצות": "followup_recommendation",
                "הכאב חמור מאוד": "recommend_contact",
                "לקבוע תור מעקב": "FLOW:booking.init",
                "default": "followup_recommendation"
            }
        },
        
        # Pain level query
        "pain_level_query": {
            "message": {
                "text": "על סולם של 1-10, כמה כואב לך באזור ההזרקה כרגע?",
                "options": ["1-3 (קל)", "4-6 (בינוני)", "7-10 (חזק)"]
            },
            "transitions": {
                "1-3 (קל)": "mild_pain_advice",
                "4-6 (בינוני)": "moderate_pain_advice",
                "7-10 (חזק)": "severe_pain_advice",
                "default": "general_pain_advice"
            }
        },
        
        # Mild pain advice
        "mild_pain_advice": {
            "message": {
                "text": "כאב קל לאחר ההזרקה הוא תופעה נורמלית. ניתן להניח קרח על האזור למשך 15-20 דקות מספר פעמים ביום. נוח והימנע מפעילות מאומצת למשך 24-48 שעות. אם הכאב נמשך יותר מ-3 ימים, צור קשר עם ד״ר וסים.",
                "options": ["תודה", "יש לי שאלה נוספת", "לקבוע תור מעקב"]
            },
            "transitions": {
                "תודה": "end_conversation",
                "יש לי שאלה נוספת": "misc_symptoms",
                "לקבוע תור מעקב": "FLOW:booking.init",
                "default": "end_conversation"
            }
        },
        
        # Recommend contacting the doctor
        "recommend_contact": {
            "message": {
                "text": "על סמך מה שתיארת, מומלץ לשוחח עם ד״ר וסים לקבלת הערכה והנחיות. ניתן ליצור קשר עם המרפאה בטלפון 0537330702 או לקבוע תור מעקב.",
                "options": ["לקבוע תור מעקב", "תודה, אתקשר למרפאה", "יש לי שאלה נוספת"]
            },
            "transitions": {
                "לקבוע תור מעקב": "FLOW:booking.init",
                "תודה, אתקשר למרפאה": "end_conversation",
                "יש לי שאלה נוספת": "misc_symptoms",
                "default": "end_conversation"
            }
        },
        
        # Waiting longer recommendation
        "wait_longer": {
            "message": {
                "text": "מומלץ להמתין מעט יותר. לפעמים לוקח 3-5 ימים עד שמתחילים להרגיש את השיפור מההזרקה. בינתיים מומלץ לנוח, להימנע ממאמץ, ולקרר את האזור אם יש נפיחות. אם אחרי 5 ימים עדיין אין שיפור, מומלץ ליצור קשר עם המרפאה.",
                "options": ["תודה, אמשיך לעקוב", "לקבוע תור מעקב ליתר ביטחון", "יש לי שאלה נוספת"]
            },
            "transitions": {
                "תודה, אמשיך לעקוב": "end_conversation",
                "לקבוע תור מעקב ליתר ביטחון": "FLOW:booking.init",
                "יש לי שאלה נוספת": "misc_symptoms",
                "default": "end_conversation"
            }
        },
        
        # Miscellaneous symptoms and questions
        "misc_symptoms": {
            "message": {
                "text": "איזו שאלה או תסמין אתה רוצה לברר?",
                "options": ["תופעות לוואי אפשריות", "כמה זמן להימנע מפעילות", "מתי אפשר לחזור לשגרה", "אחר"]
            },
            "transitions": {
                "תופעות לוואי אפשריות": "side_effects_info",
                "כמה זמן להימנע מפעילות": "activity_guidance",
                "מתי אפשר לחזור לשגרה": "recovery_timeline",
                "אחר": "recommend_contact",
                "default": "recommend_contact"
            }
        },
        
        # Information about side effects
        "side_effects_info": {
            "message": {
                "text": "תופעות לוואי שכיחות לאחר הזרקה כוללות:\n- כאב או אי נוחות באזור ההזרקה (1-2 ימים)\n- נפיחות קלה (1-3 ימים)\n- אדמומיות באזור ההזרקה (1-2 ימים)\n\nתופעות לא שכיחות שמצריכות פנייה לרופא:\n- חום גבוה\n- נפיחות חמורה או מתפשטת\n- אדמומיות חמורה או מתפשטת\n- כאב חמור שלא מגיב למשככי כאבים\n- הפרשה מאזור ההזרקה",
                "options": ["תודה", "יש לי שאלה נוספת", "אני חווה תופעת לוואי חמורה"]
            },
            "transitions": {
                "תודה": "followup_recommendation",
                "יש לי שאלה נוספת": "misc_symptoms",
                "אני חווה תופעת לוואי חמורה": "urgent_contact",
                "default": "followup_recommendation"
            }
        },
        
        # Activity guidance
        "activity_guidance": {
            "message": {
                "text": "המלצות לפעילות לאחר הזרקה:\n\n- מנוחה מלאה: 24-48 שעות הראשונות\n- פעילות מוגבלת: 3-7 ימים לאחר ההזרקה\n- הימנעות מפעילות מאומצת: 1-2 שבועות\n\nההמלצות משתנות בהתאם לסוג ההזרקה, המפרק המטופל והמצב האישי. לפרטים ספציפיים למקרה שלך, התייעץ עם ד״ר וסים.",
                "options": ["תודה", "יש לי שאלה נוספת", "לקבוע תור מעקב"]
            },
            "transitions": {
                "תודה": "followup_recommendation",
                "יש לי שאלה נוספת": "misc_symptoms",
                "לקבוע תור מעקב": "FLOW:booking.init",
                "default": "followup_recommendation"
            }
        },
        
        # Recovery timeline information
        "recovery_timeline": {
            "message": {
                "text": "זמני החלמה משוערים:\n\n1. הזרקת סטרואידים:\n- הקלה ראשונית: 24-72 שעות\n- השפעה מלאה: 1-2 שבועות\n- משך השפעה: שבועות עד חודשים\n\n2. חומצה היאלורונית:\n- הקלה ראשונית: 1-2 שבועות\n- השפעה מלאה: 4-6 שבועות\n- משך השפעה: 6-12 חודשים\n\n3. פלזמה (PRP):\n- הקלה ראשונית: 2-3 שבועות\n- השפעה מלאה: 6-8 שבועות\n- משך השפעה: חודשים עד שנה",
                "options": ["תודה", "יש לי שאלה נוספת", "לקבוע תור מעקב"]
            },
            "transitions": {
                "תודה": "followup_recommendation",
                "יש לי שאלה נוספת": "misc_symptoms",
                "לקבוע תור מעקב": "FLOW:booking.init",
                "default": "followup_recommendation"
            }
        },
        
        # Follow-up recommendation
        "followup_recommendation": {
            "message": {
                "text": "על פי המידע שסיפקת, נראה שהתהליך מתקדם כמצופה. מומלץ לקבוע תור מעקב כדי לוודא שההחלמה ממשיכה בצורה תקינה. האם תרצה לקבוע תור עכשיו?",
                "options": ["כן, לקבוע תור מעקב", "לא כרגע, אני מרגיש טוב", "יש לי שאלה נוספת"]
            },
            "transitions": {
                "כן, לקבוע תור מעקב": "FLOW:booking.init",
                "לא כרגע, אני מרגיש טוב": "end_conversation",
                "יש לי שאלה נוספת": "misc_symptoms",
                "default": "end_conversation"
            }
        },
        
        # End conversation
        "end_conversation": {
            "message": {
                "text": "תודה על השיחה. אנחנו כאן לשירותך אם תזדקק לעזרה נוספת. החלמה מהירה!",
                "options": ["חזרה לתפריט הראשי"]
            },
            "transitions": {
                "חזרה לתפריט הראשי": "FLOW:welcome.greeting",
                "default": "FLOW:welcome.greeting"
            }
        }
    }
}

# =====================
# 5. NEW PATIENT INQUIRY FLOW
# =====================
NEW_PATIENT_FLOW = {
    "name": "new_patient",
    "initial_state": "inquiry",
    "states": {
        "inquiry": {
            "message": {
                "text": "שלום! כדי שנוכל לעזור לך בצורה הטובה ביותר, אנא ספר לנו:\n1. ממה אתה סובל/מתלונן?\n2. כמה זמן קיימות התלונות?\n3. האם לקחת טיפול כלשהו עד כה?",
                "options": ["כאבי גב/צוואר", "כאבי ברכיים/מפרקים", "פריצת דיסק", "טראומה/שבר", "אחר"]
            },
            "transitions": {
                "כאבי גב/צוואר": "complaint_details",
                "כאבי ברכיים/מפרקים": "complaint_details",
                "פריצת דיסק": "complaint_details",
                "טראומה/שבר": "complaint_details",
                "אחר": "complaint_details",
                "default": "complaint_details"
            },
            "save_context": "complaint_type"
        },
        "complaint_details": {
            "message": {
                "text": "תודה. כמה זמן אתה סובל מ{complaint_type}?",
                "options": ["פחות משבוע", "שבוע עד חודש", "מעל חודש", "מעל חצי שנה"]
            },
            "transitions": {
                "פחות משבוע": "treatment_history",
                "שבוע עד חודש": "treatment_history",
                "מעל חודש": "treatment_history",
                "מעל חצי שנה": "treatment_history",
                "default": "treatment_history"
            },
            "save_context": "complaint_duration"
        },
        "treatment_history": {
            "message": {
                "text": "האם לקחת טיפול כלשהו עד כה לטיפול ב{complaint_type}?",
                "options": ["לא", "כדורים לכאבים", "פיזיותרפיה", "הזרקות קודמות", "טיפולים אחרים"]
            },
            "transitions": {
                "לא": "reassurance",
                "כדורים לכאבים": "reassurance",
                "פיזיותרפיה": "reassurance",
                "הזרקות קודמות": "reassurance",
                "טיפולים אחרים": "reassurance",
                "default": "reassurance"
            },
            "save_context": "prior_treatment"
        },
        "reassurance": {
            "message": {
                "text": "תודה על המידע. אנחנו כאן לרשותך ונעזור לך להחלים ולהתגבר על הכאב שלך. ד״ר וסים מתמחה בטיפול בבעיות כמו {complaint_type} ויוכל לתת לך טיפול מותאם אישית. האם תרצה לקבוע תור לבדיקה?",
                "options": ["כן, אשמח לקבוע תור", "מה עלות הטיפול?", "מה אפשרויות הטיפול?"]
            },
            "transitions": {
                "כן, אשמח לקבוע תור": "FLOW:booking.init",
                "מה עלות הטיפול?": "cost_info",
                "מה אפשרויות הטיפול?": "treatment_options",
                "default": "FLOW:booking.init"
            }
        },
        "cost_info": {
            "message": {
                "text": "עלות הייעוץ והטיפול הרפואי אצל ד״ר וסים היא 400 ש״ח. מחיר זה אינו כולל עלות חומרים להזרקה או הערכות נכות וחוות דעת משפטיות. האם תרצה לקבוע תור?",
                "options": ["כן, אשמח לקבוע תור", "יש לי שאלה נוספת", "תודה, אחשוב על זה"]
            },
            "transitions": {
                "כן, אשמח לקבוע תור": "FLOW:booking.init",
                "יש לי שאלה נוספת": "FLOW:welcome.greeting",
                "תודה, אחשוב על זה": "end_inquiry",
                "default": "FLOW:welcome.greeting"
            }
        },
        "treatment_options": {
            "message": {
                "text": "ד״ר וסים יציע את אפשרויות הטיפול המתאימות לאחר בדיקה מקיפה. הטיפולים עשויים לכלול: ייעוץ והכוונה, טיפול תרופתי, הזרקות (סטרואידים, חומצה היאלורונית או פלזמה), המלצה על פיזיותרפיה, או במקרים מסוימים הפניה לבדיקות נוספות. הטיפול תמיד מותאם אישית למצבך הרפואי.",
                "options": ["אשמח לקבוע תור", "שאלה נוספת", "תודה"]
            },
            "transitions": {
                "אשמח לקבוע תור": "FLOW:booking.init",
                "שאלה נוספת": "FLOW:welcome.greeting",
                "תודה": "end_inquiry",
                "default": "FLOW:welcome.greeting"
            }
        },
        "end_inquiry": {
            "message": {
                "text": "תודה שפנית אלינו. אנחנו זמינים לכל שאלה נוספת. לקביעת תור או למידע נוסף, אנא צור איתנו קשר בכל עת.",
                "options": ["חזרה לתפריט הראשי"]
            },
            "transitions": {
                "חזרה לתפריט הראשי": "FLOW:welcome.greeting",
                "default": "FLOW:welcome.greeting"
            }
        }
    }
}

# Dictionary of all available flows
CONVERSATION_FLOWS = {
    "welcome": WELCOME_FLOW,
    "catalog": CATALOG_FLOW,
    "booking": BOOKING_FLOW,
    "injected_patient": INJECTED_PATIENT_FLOW,
    "new_patient": NEW_PATIENT_FLOW
}

def get_flow(flow_name):
    """Get a specific conversation flow by name"""
    return CONVERSATION_FLOWS.get(flow_name)

def get_all_flows():
    """Get all conversation flows"""
    return CONVERSATION_FLOWS

def get_flow_state(flow_name, state_name):
    """Get a specific state within a flow"""
    flow = get_flow(flow_name)
    if not flow:
        return None
    
    states = flow.get('states', {})
    return states.get(state_name)

def get_dynamic_options(flow_state, context):
    """Generate dynamic options based on flow state and context"""
    if "date" in flow_state:
        # Generate dates for appointment booking
        day = context.get('selected_day', '')
        
        # Extract just the day name without "יום" prefix if present
        if "יום" in day:
            day = day.replace("יום ", "")
        
        # Map Hebrew days to weekday numbers (0=Monday in Python)
        day_mapping = {
            'ראשון': 6,  # Sunday
            'שני': 0,    # Monday
            'שלישי': 1,  # Tuesday
            'רביעי': 2,  # Wednesday
            'חמישי': 3,  # Thursday
            'שישי': 4,   # Friday
            'שבת': 5     # Saturday
        }
        
        # Default to Sunday if day not recognized
        weekday = day_mapping.get(day, 6)
        
        # Generate next 4 available dates for selected day
        today = datetime.now()
        dates = []
        
        current = today
        while len(dates) < 4:
            if current.weekday() == weekday:
                # Format: "DD/MM/YYYY"
                date_str = current.strftime("%d/%m/%Y")
                # Format for display: "DD/MM"
                display_date = current.strftime("%d/%m")
                dates.append(display_date)
            current += timedelta(days=1)
            
        return dates
        
    elif "time" in flow_state:
        # Generate time slots
        day = context.get('selected_day', '')
        
        # Different schedules based on day
        if "ראשון" in day:
            return ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00", "18:00"]
        elif "שלישי" in day:
            return ["10:00", "11:00", "12:00", "13:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
        elif "חמישי" in day:
            return ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00", "17:00"]
        else:
            # Default time slots
            return ["09:00", "11:00", "13:00", "15:00", "17:00"]
    
    # Default empty options
    return []

def process_flow_transition(flow_name, current_state, user_input, context=None):
    """
    Process a user input within a conversation flow and determine the next state
    
    Args:
        flow_name (str): Name of the current flow
        current_state (str): Current state in the flow
        user_input (str): User's input/selection
        context (dict): Current context data
        
    Returns:
        tuple: (next_flow, next_state, response, updated_context)
    """
    context = context or {}
    flow = get_flow(flow_name)
    
    if not flow:
        logger.warning(f"Flow '{flow_name}' not found")
        return "welcome", "greeting", WELCOME_FLOW["states"]["greeting"]["message"], context
    
    states = flow.get('states', {})
    current_state_data = states.get(current_state)
    
    if not current_state_data:
        logger.warning(f"State '{current_state}' not found in flow '{flow_name}'")
        return "welcome", "greeting", WELCOME_FLOW["states"]["greeting"]["message"], context
    
    # Save context if specified
    if 'save_context' in current_state_data and user_input:
        context_key = current_state_data['save_context']
        context[context_key] = user_input
        # Add debug log
        logger.info(f"Saved to context: {context_key}={user_input}")
    
    # Get transitions from current state
    transitions = current_state_data.get('transitions', {})
    
    # Determine next state based on user input
    next_transition = None
    
    # Check if user input matches any specific transition
    if user_input in transitions:
        next_transition = transitions[user_input]
        # Add debug log
        logger.debug(f"Found exact transition for '{user_input}': {next_transition}")
    else:
        # Use default transition
        next_transition = transitions.get('default')
        logger.debug(f"Using default transition: {next_transition}")
    
    # If next_transition is a string, it's a direct state reference
    if isinstance(next_transition, str):
        # Check if it's a flow change
        if next_transition.startswith("FLOW:"):
            # Format: "FLOW:flow_name.state_name"
            flow_state = next_transition[5:].split('.')
            next_flow = flow_state[0]
            next_state = flow_state[1] if len(flow_state) > 1 else "init"
            
            # Add debug log
            logger.info(f"Transitioning to new flow: {next_flow}.{next_state}")
            
            # Get the message for the next state
            next_flow_data = get_flow(next_flow)
            if not next_flow_data:
                logger.warning(f"Target flow '{next_flow}' not found")
                return "welcome", "greeting", WELCOME_FLOW["states"]["greeting"]["message"], context
                
            next_state_data = next_flow_data["states"].get(next_state)
            if not next_state_data:
                logger.warning(f"Target state '{next_state}' not found in flow '{next_flow}'")
                return "welcome", "greeting", WELCOME_FLOW["states"]["greeting"]["message"], context
                
            response = next_state_data.get('message', {})
            
            # Process dynamic options
            if "options" in response and "DYNAMIC" in str(response["options"]):
                dynamic_options = get_dynamic_options(next_state, context)
                if dynamic_options:
                    response["options"] = dynamic_options
                    # Store the options in context for later validation
                    context[f"{next_state}_options"] = dynamic_options
            
            return next_flow, next_state, response, context
        else:
            # It's a state in the same flow
            next_state = next_transition
            
            # Add debug log
            logger.info(f"Transitioning to new state in same flow: {flow_name}.{next_state}")
            
            next_state_data = states.get(next_state)
            
            if not next_state_data:
                logger.warning(f"Next state '{next_state}' not found in flow '{flow_name}'")
                return "welcome", "greeting", WELCOME_FLOW["states"]["greeting"]["message"], context
                
            response = next_state_data.get('message', {})
            
            # Process dynamic options
            if "options" in response and "DYNAMIC" in str(response["options"]):
                dynamic_options = get_dynamic_options(next_state, context)
                if dynamic_options:
                    response["options"] = dynamic_options
                    # Store the options in context for later validation
                    context[f"{next_state}_options"] = dynamic_options
            
            # Make sure we're returning to the same flow
            return flow_name, next_state, response, context

    # Special handling for injection topics
    if flow_name == "catalog" and current_state == "injections":
        treatment_map = {
            "הזרקת סטרואידים": "steroids",
            "חומצה היאלורונית": "hyaluronic",
            "טיפול בפלזמה (PRP)": "prp"
        }
        
        if user_input in treatment_map:
            topic = treatment_map[user_input]
            next_state = topic
            
            # Get the detailed information about this topic
            from .response_generator import generate_expanded_information
            
            # Create a response with the detailed information
            treatment_name = user_input.replace("(PRP)", "").strip()
            detailed_info = generate_expanded_information(treatment_name, context)
            
            response = {
                "text": detailed_info,
                "options": ["לקבוע תור לטיפול זה", "מחירים", "חזרה לסוגי הזרקות"]
            }
            
            # Update context with the selected treatment
            if context is None:
                context = {}
            context['selected_treatment'] = treatment_name
            context['last_topic'] = treatment_name
            
            return flow_name, next_state, response, context
    
    # If we got here, something went wrong with the transition
    logger.warning(f"Invalid transition for input '{user_input}' in state '{current_state}' of flow '{flow_name}'")
    return "welcome", "greeting", WELCOME_FLOW["states"]["greeting"]["message"], context

# Add a function to handle open-ended questions during flows
def handle_open_question(question_text, current_flow, current_state, context):
    """
    Handle open-ended questions that might come up during a structured flow
    
    Args:
        question_text (str): User's question
        current_flow (str): Current conversation flow
        current_state (str): Current state in the flow
        context (dict): Current conversation context
        
    Returns:
        dict: Response with guidance to continue the flow
    """
    # Try to identify question topic
    medical_keywords = {
        "כאב": "תחושת כאב היא סימן שהגוף שולח כדי להתריע על בעיה. ד״ר וסים מתמחה באבחון מקור הכאב ובטיפול בו.",
        "נפיחות": "נפיחות יכולה להעיד על דלקת או בצקת באזור. חשוב לאבחן את הסיבה לנפיחות כדי לטפל בה ביעילות.",
        "שיקום": "תהליך השיקום הוא חלק חשוב מההחלמה. ד״ר וסים יתאים לך תכנית שיקום אישית בהתאם למצבך.",
        "תרופות": "הטיפול התרופתי צריך להיות מותאם אישית בהתאם לאבחנה, חומרת המצב וגורמים אישיים נוספים.",
        "ניתוח": "ד״ר וסים מאמין בניסיון טיפולים שמרניים לפני פנייה לניתוח, אך במקרים מסוימים ניתוח הוא האופציה הטובה ביותר."
    }
    
    # Check if any of the medical keywords are in the question
    response_text = None
    for keyword, explanation in medical_keywords.items():
        if keyword in question_text:
            response_text = explanation
            break
    
    # Default response if no specific medical keyword was found
    if not response_text:
        response_text = "זו שאלה חשובה. ד״ר וסים יוכל לענות עליה בצורה מקיפה במהלך הפגישה, תוך התחשבות במצבך האישי."
    
    # Return a response that acknowledges the question but keeps the flow going
    return {
        "text": f"{response_text}\n\nנמשיך בשיחה שלנו?",
        "options": ["כן, בהחלט", "יש לי שאלה נוספת", "אני רוצה לקבוע תור"],
        "flow": current_flow,
        "state": current_state
    }
