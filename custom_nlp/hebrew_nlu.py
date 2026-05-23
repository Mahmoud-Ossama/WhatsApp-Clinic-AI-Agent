"""
Advanced Hebrew Natural Language Understanding module
Uses word embeddings and semantic similarity for better intent matching
"""
import re
import logging
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import word_tokenize
from collections import Counter
import string
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

# Extended intent examples for training
INTENT_EXAMPLES = {
    "greeting": [
        "שלום", "היי", "בוקר טוב", "ערב טוב", "מה שלומך", "מה נשמע", 
        "אהלן", "שלום לך", "בוקר אור", "ערב טוב", "צהריים טובים"
    ],
    "appointment_request": [
        "אני רוצה לקבוע תור", "אפשר לקבוע תור?", "מתי יש תורים פנויים?",
        "איך אני קובע תור?", "תור לרופא", "זימון תור", "תיאום פגישה",
        "אני צריך תור", "מתי אפשר להגיע?", "פגישה עם הרופא", "לקבוע פגישה"
    ],
    "services": [
        "אילו שירותים אתם מספקים?", "מה השירותים שלכם?", "מה אתם מציעים?",
        "איזה טיפולים יש?", "מה אפשר לעשות אצלכם?", "איזה שירותים?", 
        "אתם עושים הזרקות?", "יש לכם טיפולי גב?", "אילו טיפולים?",
        "מהם השירותים?", "מה הטיפולים?", "אילו פתרונות אתם מציעים?",
        "שירותים", "טיפולים", "אפשרויות טיפול", "מה אתם עושים?",
        "מה יש במרפאה?", "איזה מומחיות?", "מה אפשר לטפל אצלכם?"
    ],
    "prices": [
        "כמה עולה?", "מה המחיר?", "מחירים", "עלויות", "תעריף", 
        "כמה זה יעלה לי?", "מה העלות?", "כמה עולה טיפול?", 
        "מחירון", "האם זה יקר?", "תעריפים", "מה המחירים?",
        "כמה לשלם?", "עלות טיפול"
    ],
    "doctor_info": [
        "מי הדוקטור?", "ספר לי על הרופא", "מיהו ד\"ר וסים?", 
        "ניסיון של הרופא", "מומחיות של הדוקטור", "רקע של הרופא",
        "איפה למד הרופא?", "התמחות של הדוקטור", "כמה שנות ניסיון?",
        "מידע על הרופא", "פרטים על ד\"ר וסים", "מי המומחה?"
    ],
    "injections": [
        "הזרקות", "הזרקה למפרק", "זריקה לברך", "הזרקת סטרואידים",
        "טיפול בהזרקה", "זריקות", "PRP", "חומצה היאלורונית",
        "הזרקה לכאבים", "הזרקה לגב", "הזרקות מפרקים",
        "סוגי הזרקות", "הזרקות כאב", "זריקות לכאבים"
    ],
    "location": [
        "איפה אתם?", "איפה המרפאה?", "כתובת", "מיקום", 
        "איך מגיעים?", "איפה אתם נמצאים?", "הכתובת שלכם",
        "מיקום המרפאה", "איך להגיע?", "המקום שלכם", "היכן אתם?"
    ]
}

# Add specific treatment intents
INTENT_EXAMPLES["prp_info"] = [
    "מהי הזרקת פלזמה", "מה זה PRP", "ספר לי על פלזמה", "מה זה טיפול בפלזמה",
    "איך עובד טיפול PRP", "טיפול בפלזמה", "הזרקת פלזמה", "PRP"
]

INTENT_EXAMPLES["hyaluronic_info"] = [
    "מהי חומצה היאלורונית", "מה זה הזרקת חומצה היאלורונית",
    "חומצה היאלורונית", "ספר לי על חומצה היאלורונית"
]

INTENT_EXAMPLES["steroids_info"] = [
    "מהם סטרואידים", "מה זה הזרקת סטרואידים", "סטרואידים",
    "ספר לי על הזרקת סטרואידים", "הזרקת סטרואידים"
]

# Stopwords in Hebrew - common words to ignore for better matching
HEBREW_STOPWORDS = [
    "את", "של", "ה", "ב", "ל", "עם", "על", "זה", "זו", "אני", "הוא", "היא", 
    "אנחנו", "הם", "הן", "אתה", "אתם", "אתן", "אשר", "כי", "כאשר", "אם", "או"
]

# Define Hebrew intents with examples
HEBREW_INTENTS = {
    'greeting': [
        'שלום', 'היי', 'בוקר טוב', 'ערב טוב', 'צהריים טובים', 'מה שלומך',
        'שלום וברכה', 'שלום לך', 'אהלן', 'מה נשמע', 'אהלן וסהלן'
    ],
    'doctor_info': [
        'מי זה דר וסים', 'ספר לי על הרופא', 'מה ההתמחות של דר וסים',
        'מיהו דר וסים אלעוברה', 'מה הרקע של הרופא', 'מה הניסיון של דר וסים',
        'מה התמחות הרופא', 'רקע מקצועי של דר וסים', 'מי הרופא', 'מידע על הדוקטור'
    ],
    'services': [
        'אילו שירותים מציעים', 'מה השירותים שלכם', 'מה אתם מציעים במרפאה',
        'אילו טיפולים יש', 'מה הטיפולים הזמינים', 'איזה שירותים רפואיים',
        'מה ניתן לעשות במרפאה', 'איזה טיפולים קיימים', 'שירותים במרפאה'
    ],
    'injection_types': [
        'סוגי הזרקות', 'אילו הזרקות יש', 'מה ההבדל בין ההזרקות', 
        'הזרקות למפרקים', 'הזרקת סטרואידים', 'חומצה היאלורונית',
        'פלזמה עשירה בטסיות', 'הזרקת PRP', 'הזרקת קורטיזון', 
        'הזרקה לברך', 'הזרקה לכתף', 'הזרקה לגב', 'הזרקה למרפק'
    ],
    'post_injection': [
        'כאב אחרי הזרקה', 'תופעות לוואי מהזרקה', 'כואב לי אחרי ההזרקה',
        'יש לי נפיחות אחרי הזרקה', 'המפרק נפוח אחרי הזרקה', 'חום לאחר הזרקה',
        'אודם במקום ההזרקה', 'כמה זמן כואב אחרי הזרקה', 'כמה זמן הכאב נמשך לאחר הזרקה'
    ],
    'pricing': [
        'כמה עולה', 'מה המחיר', 'עלויות', 'מחירון', 'תעריף', 'כמה עולה הטיפול',
        'מחיר הזרקה', 'עלות ייעוץ', 'תעריפים', 'האם זה כלול בקופת חולים',
        'האם מכוסה בביטוח', 'עלות בדיקה', 'מחיר בדיקה'
    ],
    'booking': [
        'קביעת תור', 'איך קובעים תור', 'ברצוני לקבוע תור', 'אני רוצה להגיע לבדיקה',
        'הזמנת תור', 'לקבוע פגישה', 'זימון תור', 'מתי אפשר להגיע', 'שעות פעילות',
        'אפשר לקבוע תור דחוף', 'איך מזמינים תור', 'קביעת תור לבדיקה'
    ],
    'children_services': [
        'טיפול בילדים', 'אורתופדיה ילדים', 'בדיקות ילדים', 'טיפול בתינוקות',
        'בעיות במפרק ירך אצל תינוקות', 'דיספלזיה של הירך', 'תינוק צולע',
        'כף רגל קלאב פוט', 'רגליים מעוקמות אצל ילדים', 'עקמת'
    ],
    'ultrasound': [
        'אולטרסאונד', 'בדיקת אולטרסאונד', 'US למפרקים', 'אולטרסאונד ירך',
        'אולטרסאונד לתינוקות', 'בדיקת סאונד'
    ],
    'disability_assessment': [
        'הערכת נכות', 'ביטוח לאומי', 'אחוזי נכות', 'חוות דעת לביטוח לאומי',
        'ועדה רפואית', 'בדיקה לביטוח לאומי', 'נכות רפואית'
    ],
    'legal_opinion': [
        'חוות דעת משפטית', 'דוח רפואי למשפט', 'חוות דעת מומחה',
        'דוח לעורך דין', 'חוות דעת לתביעה', 'משרד הביטחון'
    ],
    'pain_complaint': [
        'כואב לי', 'סובל מכאבים', 'יש לי כאב', 'כאב ברגל', 'כאב בברך',
        'כאב בגב', 'כואבת לי הכתף', 'כאב מפרקים', 'סובל מדלקת',
        'כאב בצוואר', 'כאב עז', 'כאב כרוני'
    ]
}

# Define entity patterns
ENTITY_PATTERNS = {
    'joint': r'(?:ברך|כתף|מרפק|קרסול|ירך|גב|צוואר|יד|רגל|מפרק)',
    'injection_type': r'(?:סטרואיד|קורטיזון|היאלורונית|חומצה|פלזמה|PRP)',
    'symptom': r'(?:כאב|נפיחות|אודם|חום|דלקת|נוקשות|הגבלה בתנועה)'
}

# Setup logging
logger = logging.getLogger(__name__)

# Download necessary NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

class HebrewNLUProcessor:
    """Hebrew NLU processor using vectorization and similarity matching"""
    
    def __init__(self):
        """Initialize the NLU processor"""
        # Create vectorizer for text features
        self.vectorizer = CountVectorizer(
            analyzer='word',
            tokenizer=self._tokenize,
            lowercase=True,
            stop_words=HEBREW_STOPWORDS,
            ngram_range=(1, 2)  # Use both unigrams and bigrams
        )
        
        # Prepare training data and fit the vectorizer
        self._prepare_training_data()
        
        # Cache for optimization
        self._cache = {}
        
    def _tokenize(self, text):
        """Tokenize Hebrew text and normalize"""
        # Simple whitespace tokenization for Hebrew
        tokens = text.split()
        # Remove common punctuation
        tokens = [t.strip(',.?!:;"\'()[]{}') for t in tokens]
        # Remove empty tokens
        tokens = [t for t in tokens if t]
        return tokens
    
    def _prepare_training_data(self):
        """Prepare and vectorize the training data"""
        # Flatten all examples into a single list
        all_examples = []
        self.intent_indices = {}
        
        idx = 0
        for intent, examples in INTENT_EXAMPLES.items():
            start_idx = idx
            for example in examples:
                all_examples.append(example)
                idx += 1
            self.intent_indices[intent] = (start_idx, idx - 1)
        
        # Fit the vectorizer
        self.X = self.vectorizer.fit_transform(all_examples)
        self.feature_names = self.vectorizer.get_feature_names_out()
        
    def get_intent(self, text, threshold=0.2):
        """
        Determine the intent of a text input
        
        Args:
            text (str): Input text
            threshold (float): Minimum similarity threshold
            
        Returns:
            tuple: (intent_name, confidence_score)
        """
        # Check cache first
        if text in self._cache:
            return self._cache[text]
        
        # Vectorize the input text
        text_vector = self.vectorizer.transform([text])
        
        # Calculate cosine similarity with all examples
        similarities = cosine_similarity(text_vector, self.X)[0]
        
        # Find the intent with the highest average similarity
        best_intent = None
        best_score = 0
        
        for intent, (start_idx, end_idx) in self.intent_indices.items():
            # Get similarities for this intent's examples
            intent_similarities = similarities[start_idx:end_idx+1]
            # Take the max similarity as the score
            score = np.max(intent_similarities) if len(intent_similarities) > 0 else 0
            
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # If score is below threshold, return "unknown"
        if best_score < threshold:
            result = ("unknown", best_score)
        else:
            result = (best_intent, best_score)
            
        # Cache the result
        self._cache[text] = result
        return result
    
    def extract_entities(self, text):
        """
        Extract entities from the text
        
        Args:
            text (str): Input text
            
        Returns:
            dict: Extracted entities
        """
        entities = {}
        
        # Body parts
        body_parts = ["ראש", "צוואר", "גב", "כתף", "מרפק", "יד", "ברך", "ירך", "רגל"]
        found_parts = [part for part in body_parts if part in text]
        if found_parts:
            entities["body_part"] = found_parts
        
        # Treatment types
        treatments = ["הזרקה", "פיזיותרפיה", "טיפול", "ניתוח", "סטרואידים", "PRP"]
        found_treatments = [t for t in treatments if t in text]
        if found_treatments:
            entities["treatment"] = found_treatments
        
        # Extract dates and times (simplified)
        date_pattern = r'\b\d{1,2}[/.-]\d{1,2}([/.-]\d{2,4})?\b'
        time_pattern = r'\b\d{1,2}:\d{2}\b'
        
        date_matches = re.findall(date_pattern, text)
        time_matches = re.findall(time_pattern, text)
        
        if date_matches:
            entities["date"] = date_matches[0]
        if time_matches:
            entities["time"] = time_matches[0]
            
        return entities

# Initialize a global instance
nlu_processor = HebrewNLUProcessor()

def get_intent(text):
    """
    Get the intent and confidence score for a text input
    
    Args:
        text (str): Input text
        
    Returns:
        tuple: (intent_name, confidence_score)
    """
    return nlu_processor.get_intent(text)

def extract_entities(text):
    """
    Extract entities from text
    
    Args:
        text (str): Input text
        
    Returns:
        dict: Extracted entities
    """
    return nlu_processor.extract_entities(text)

def understand_hebrew_text(text):
    """
    Comprehensive understanding of Hebrew text input
    
    Args:
        text (str): Input text
        
    Returns:
        dict: Understanding results with intent and entities
    """
    # Check for direct questions about topics first
    direct_question_keywords = {
        "פלזמה": "prp_info",
        "PRP": "prp_info",
        "סטרואידים": "steroids_info",
        "היאלורונית": "hyaluronic_info",
        "חומצה היאלורונית": "hyaluronic_info",
    }
    
    # First check for very explicit questions
    for keyword, intent in direct_question_keywords.items():
        patterns = [
            rf"מהי\s+(?:[א-ת\s]+\s)?{keyword}",
            rf"מה\s+זה\s+(?:[א-ת\s]+\s)?{keyword}",
            rf"ספר\s+לי\s+על\s+(?:[א-ת\s]+\s)?{keyword}",
            rf"מידע\s+על\s+(?:[א-ת\s]+\s)?{keyword}"
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns) or keyword == text.strip():
            logger.debug(f"Direct topic question detected: {intent} for topic {keyword}")
            entities = extract_entities(text)
            entities['treatment_type'] = [keyword]
            entities['topic'] = keyword
            return {
                "intent": intent,
                "confidence": 0.95,
                "entities": entities,
                "original_text": text
            }
    
    # Continue with regular intent detection
    intent, confidence = get_intent(text)
    entities = extract_entities(text)
    
    logger.debug(f"Hebrew NLU: Intent={intent}, Confidence={confidence:.4f}, Entities={entities}")
    
    # Enhance entity detection for topics
    for keyword in direct_question_keywords:
        if keyword in text:
            entities.setdefault('treatment_type', []).append(keyword)
            entities['topic'] = keyword
    
    return {
        "intent": intent,
        "confidence": confidence,
        "entities": entities,
        "original_text": text
    }

def preprocess_hebrew_text(text):
    """Clean and normalize Hebrew text."""
    if not text:
        return ""
    
    # Remove punctuation and normalize spaces
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_entities(text):
    """Extract relevant entities from the text."""
    entities = {}
    
    for entity_type, pattern in ENTITY_PATTERNS.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        if matches:
            entities[entity_type] = [match.group(0) for match in matches]
    
    return entities

def detect_intent(text):
    """Detect the intent of a Hebrew message using TF-IDF and cosine similarity."""
    if not text or not text.strip():
        return {'intent': 'greeting', 'confidence': 1.0, 'entities': {}}
    
    # Preprocess the input text
    processed_text = preprocess_hebrew_text(text)
    
    # If text is very short (1-2 words), check for direct matches first
    if len(processed_text.split()) <= 2:
        for intent, examples in HEBREW_INTENTS.items():
            if processed_text in examples:
                return {
                    'intent': intent,
                    'confidence': 1.0,
                    'entities': extract_entities(text)
                }
    
    # Prepare all examples and the input text
    all_examples = []
    intent_indices = {}
    current_idx = 0
    
    for intent, examples in HEBREW_INTENTS.items():
        processed_examples = [preprocess_hebrew_text(ex) for ex in examples]
        all_examples.extend(processed_examples)
        intent_indices[intent] = list(range(current_idx, current_idx + len(processed_examples)))
        current_idx += len(processed_examples)
    
    # Add the input text at the end
    all_examples.append(processed_text)
    
    # Create TF-IDF vectorizer and compute similarities
    try:
        vectorizer = TfidfVectorizer(tokenizer=lambda x: x.split())
        tfidf_matrix = vectorizer.fit_transform(all_examples)
        
        # Compute cosine similarity between input text and all examples
        cosine_similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
        
        # Find the intent with the highest similarity
        max_similarity = np.max(cosine_similarities)
        if max_similarity < 0.1:  # Confidence threshold
            best_intent = 'fallback'
            confidence = 0.0
        else:
            best_example_idx = np.argmax(cosine_similarities)
            confidence = max_similarity
            
            # Find which intent this example belongs to
            best_intent = None
            for intent, indices in intent_indices.items():
                if best_example_idx in indices:
                    best_intent = intent
                    break
            
            if best_intent is None:
                best_intent = 'fallback'
                confidence = 0.0
    
    except Exception as e:
        logger.error(f"Error in intent detection: {str(e)}")
        best_intent = 'fallback'
        confidence = 0.0
    
    # Extract entities
    entities = extract_entities(text)
    
    return {
        'intent': best_intent,
        'confidence': float(confidence),
        'entities': entities
    }
