from datetime import datetime
from flask_login import UserMixin
from pymongo import MongoClient
from bson import ObjectId

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['dr_wasim_db']

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
        self.created_at = datetime.utcnow()
