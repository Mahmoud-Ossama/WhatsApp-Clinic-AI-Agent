from datetime import datetime
from flask_login import UserMixin
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection using environment variables
client = MongoClient(os.getenv('MONGODB_URI'))
db = client[os.getenv('MONGODB_DB_NAME', 'dr_wasim_db')]

class User(UserMixin):
    def __init__(self, username, password_hash, role='doctor'):
        self.username = username
        self.password_hash = password_hash
        self.role = role
        
    @staticmethod
    def get(user_id):
        user_data = db.users.find_one({'_id': ObjectId(user_id)})
        if not user_data:
            return None
        user = User(
            username=user_data['username'],
            password_hash=user_data['password_hash'],
            role=user_data.get('role', 'doctor')
        )
        user.id = str(user_data['_id'])
        return user

class Patient:
    collection = db.patients

    def __init__(self, name, phone, medical_history=None, status='active'):
        self.name = name
        self.phone = phone
        self.medical_history = medical_history or {}
        self.status = status
        self.created_at = datetime.utcnow()

    @staticmethod
    def get_all():
        return list(db.patients.find())

class Injection:
    collection = db.injections

    def __init__(self, patient_id, date, injection_type, dosage, notes=None):
        self.patient_id = patient_id
        self.date = date
        self.type = injection_type
        self.dosage = dosage
        self.notes = notes
        self.next_followup = None
        self.created_at = datetime.utcnow()

class FollowUp:
    collection = db.followups

    def __init__(self, injection_id, patient_id, scheduled_date):
        self.injection_id = injection_id
        self.patient_id = patient_id
        self.scheduled_date = scheduled_date
        self.status = 'pending'
        self.responses = []
        self.patient_response = None  # Store patient's response
        self.response_date = None     # When the patient responded
        self.created_at = datetime.utcnow()
    
    @staticmethod
    def update_patient_response(phone, response_text):
        """Add a response from a patient based on their phone number"""
        try:
            # Log for debugging
            print(f"⏺️ Processing response from phone: {phone}")
            
            # Try different phone formats
            phone_formats = [
                phone,
                phone.replace('+', ''),
                phone.lstrip('0'),
                '0' + phone.lstrip('0'),
                '+' + phone.lstrip('+').lstrip('0'),
                # Additional formats specific to Israeli/Palestinian numbers
                phone.replace('+972', '0'),
                phone.replace('972', '0'),
                # If number starts with 05, also try country code format
                '+972' + phone[1:] if phone.startswith('0') else None,
                '972' + phone[1:] if phone.startswith('0') else None,
            ]
            phone_formats = [p for p in phone_formats if p]  # Remove None values
            
            # Try to find patient with any of these formats
            patient = None
            matched_format = None
            
            print(f"⏺️ Trying phone formats: {phone_formats}")
            
            for fmt in phone_formats:
                patient = db.patients.find_one({'phone': fmt})
                if patient:
                    matched_format = fmt
                    print(f"✅ Found patient with phone: {fmt}")
                    break
            
            if not patient:
                print(f"❌ No patient found with any phone format. Original: {phone}")
                return False
            
            print(f"✅ Found patient: {patient.get('name')}")
            
            # Create a new followup response record directly
            response_id = db.followups.update_one(
                {
                    'patient_id': patient['_id'],
                    'patient_response': None,  # Only update if no previous response
                    'status': 'pending'
                },
                {
                    '$set': {
                        'patient_response': response_text,
                        'response_date': datetime.utcnow(),
                        'status': 'responded'
                    }
                }
            )
            
            if response_id.modified_count > 0:
                print(f"✅ Successfully recorded response for {patient.get('name')}")
                return True
            else:
                # If no pending followup was updated, create a new one
                followup_id = db.followups.insert_one({
                    'patient_id': patient['_id'],
                    'patient_name': patient['name'],
                    'patient_phone': matched_format,
                    'scheduled_date': datetime.utcnow(),
                    'patient_response': response_text,
                    'response_date': datetime.utcnow(),
                    'status': 'responded',
                    'created_at': datetime.utcnow()
                }).inserted_id
                
                print(f"✅ Created new followup with response for {patient.get('name')}")
                return True
        except Exception as e:
            print(f"❌ Error in update_patient_response: {e}")
            import traceback
            traceback.print_exc()
            return False
