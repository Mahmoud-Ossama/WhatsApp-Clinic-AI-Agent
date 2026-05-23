from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.actions import action
from flask_admin.contrib.pymongo import ModelView
from flask_admin.form import rules
from flask_login import current_user, login_required
from flask import flash
from wtforms import form, fields
from wtforms.validators import DataRequired
from bson import ObjectId
from datetime import datetime, date, timedelta
import logging
from .models import db
import sys
import os

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.whatsapp import send_immediate_message, send_followup_message

logger = logging.getLogger(__name__)

class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

class PatientForm(form.Form):
    name = fields.StringField('الاسم', validators=[DataRequired()])
    phone = fields.StringField('رقم الهاتف', validators=[DataRequired()])
    nationality = fields.SelectField('الجنسية', choices=[
        ('arab', 'عربي'),
        ('israeli', 'عبري')
    ])
    injection_status = fields.SelectField('حالة الحقن', choices=[
        ('injected', 'محقون'),
        ('not_injected', 'غير محقون')
    ])
    medical_date = fields.DateField('التاريخ المرضي', default=datetime.now)
    status = fields.SelectField('الحالة', choices=[
        ('active', 'نشط'),
        ('inactive', 'غير نشط')
    ])

class PatientView(AdminModelView):
    column_list = ('name', 'phone', 'nationality', 'injection_status', 'medical_date', 'status', 'created_at')
    column_labels = {
        'name': 'الاسم',
        'phone': 'رقم الهاتف',
        'nationality': 'الجنسية',
        'injection_status': 'حالة الحقن',
        'medical_date': 'التاريخ المرضي',
        'status': 'الحالة',
        'created_at': 'تاريخ التسجيل'
    }
    form = PatientForm
    
    # Enable bulk actions
    can_export = True
    action_disallowed_list = []
    
    # Configure the batch actions and their Arabic labels
    action_form_args = {
        'action': {
            'choices': [
                ('mark_as_injected', 'تحديد كمحقونين'),
                ('mark_as_not_injected', 'تحديد كغير محقونين'),
                ('mark_as_active', 'تحديد كنشطين'),
                ('mark_as_inactive', 'تحديد كغير نشطين'),
                ('send_followup_message', 'إرسال رسالة متابعة'),
                ('send_appointment_reminder', 'إرسال تذكير بالموعد'),
            ]
        }
    }
    
    column_formatters = {
        'medical_date': lambda v, c, m, p: m['medical_date'].strftime('%Y-%m-%d') if m.get('medical_date') else '',
        'created_at': lambda v, c, m, p: m['created_at'].strftime('%Y-%m-%d') if m.get('created_at') else ''
    }
    
    @action('mark_as_injected', 'تحديد كمحقونين', 'هل أنت متأكد من تحديد المرضى المحددين كمحقونين؟')
    def action_mark_as_injected(self, ids):
        try:
            # Update all selected patients to be marked as injected
            for patient_id in ids:
                patient = db.patients.find_one({'_id': ObjectId(patient_id)})
                
                # Only update if the current status is different
                if patient and patient.get('injection_status') != 'injected':
                    db.patients.update_one(
                        {'_id': ObjectId(patient_id)},
                        {'$set': {'injection_status': 'injected'}}
                    )
                    
                    # Schedule followup message for 2 days later
                    try:
                        phone = patient.get('phone')
                        if phone:
                            if not phone.startswith('+'):
                                phone = '+' + phone
                            
                            nationality = patient.get('nationality', 'arab')
                            patient_name = patient.get('name', '')
                            
                            # Schedule the message instead of sending immediately
                            from utils.whatsapp import schedule_injection_followup
                            message_id = schedule_injection_followup(
                                patient_id=str(patient['_id']),
                                phone=phone,
                                patient_name=patient_name,
                                nationality=nationality,
                                delay_days=2  # Schedule for 2 days later
                            )
                            
                            if message_id:
                                # Record the scheduled followup
                                scheduled_date = datetime.utcnow() + timedelta(days=2)
                                db.followups.insert_one({
                                    'patient_id': patient['_id'],
                                    'patient_name': patient.get('name', ''),
                                    'status': 'scheduled',
                                    'scheduled_date': scheduled_date,
                                    'message_type': 'post_injection',
                                    'phone': phone,
                                    'scheduled_message_id': message_id
                                })
                                logger.info(f"Injection followup message scheduled for {phone}")
                    except Exception as e:
                        logger.error(f"Error scheduling message for {patient_id}: {str(e)}")
                        
            flash(f'تم تحديث {len(ids)} من المرضى بنجاح', 'success')
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    @action('mark_as_not_injected', 'تحديد كغير محقونين', 'هل أنت متأكد من تحديد المرضى المحددين كغير محقونين؟')
    def action_mark_as_not_injected(self, ids):
        try:
            # Update all selected patients to be marked as not injected
            count = 0
            for patient_id in ids:
                result = db.patients.update_one(
                    {'_id': ObjectId(patient_id), 'injection_status': 'injected'},
                    {'$set': {'injection_status': 'not_injected'}}
                )
                if result.modified_count > 0:
                    count += 1
            
            flash(f'تم تحديث {count} من المرضى بنجاح', 'success')
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    @action('mark_as_active', 'تحديد كنشطين', 'هل أنت متأكد من تحديد المرضى المحددين كنشطين؟')
    def action_mark_as_active(self, ids):
        try:
            # Update all selected patients to be marked as active
            count = 0
            for patient_id in ids:
                result = db.patients.update_one(
                    {'_id': ObjectId(patient_id), 'status': 'inactive'},
                    {'$set': {'status': 'active'}}
                )
                if result.modified_count > 0:
                    count += 1
            
            flash(f'تم تحديث {count} من المرضى بنجاح', 'success')
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    @action('mark_as_inactive', 'تحديد كغير نشطين', 'هل أنت متأكد من تحديد المرضى المحددين كغير نشطين؟')
    def action_mark_as_inactive(self, ids):
        try:
            # Update all selected patients to be marked as inactive
            count = 0
            for patient_id in ids:
                result = db.patients.update_one(
                    {'_id': ObjectId(patient_id), 'status': 'active'},
                    {'$set': {'status': 'inactive'}}
                )
                if result.modified_count > 0:
                    count += 1
            
            flash(f'تم تحديث {count} من المرضى بنجاح', 'success')
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    @action('send_followup_message', 'إرسال رسالة متابعة', 'هل أنت متأكد من إرسال رسالة متابعة للمرضى المحددين؟')
    def action_send_followup_message(self, ids):
        try:
            # Send followup message to selected patients
            success_count = 0
            for patient_id in ids:
                try:
                    patient = db.patients.find_one({'_id': ObjectId(patient_id)})
                    if patient:
                        phone = patient.get('phone')
                        if phone:
                            if not phone.startswith('+'):
                                phone = '+' + phone
                            
                            nationality = patient.get('nationality', 'arab')
                            language = 'he' if nationality == 'israeli' else 'ar'
                            patient_name = patient.get('name', '')
                            
                            from utils.whatsapp import send_followup_message
                            next_appointment = datetime.now() + timedelta(days=14)  # Default followup in 2 weeks
                            
                            response = send_followup_message(
                                phone=phone,
                                nationality=nationality,
                                next_appointment=next_appointment
                            )
                            
                            if response:
                                # Record the followup
                                db.followups.insert_one({
                                    'patient_id': patient['_id'],
                                    'patient_name': patient_name,
                                    'status': 'pending',
                                    'scheduled_date': next_appointment,
                                    'sent_at': datetime.utcnow(),
                                    'message_type': 'followup_check',
                                    'phone': phone
                                })
                                success_count += 1
                except Exception as e:
                    logger.error(f"Error sending followup message to {patient_id}: {str(e)}")
            
            flash(f'تم إرسال رسائل المتابعة بنجاح إلى {success_count} من المرضى', 'success')
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'error')
    
    def on_model_change(self, form, model, is_created):
        # Handle dates
        if isinstance(form.medical_date.data, date):
            model['medical_date'] = datetime.combine(form.medical_date.data, datetime.min.time())
        elif isinstance(form.medical_date.data, str):
            try:
                model['medical_date'] = datetime.strptime(form.medical_date.data, '%Y-%m-%d')
            except ValueError:
                model['medical_date'] = datetime.now()
        
        # Add created_at timestamp for new records
        if is_created:
            model['created_at'] = datetime.now()
            
        # Schedule followup message if patient is marked as injected
        if form.injection_status.data == 'injected':
            old_status = None
            if not is_created:
                try:
                    old_patient = db.patients.find_one({'_id': model['_id']})
                    old_status = old_patient.get('injection_status') if old_patient else None
                except KeyError:
                    # Handle case where _id is not available yet
                    old_status = None
                except Exception as e:
                    logger.error(f"Error retrieving old patient status: {e}")
                    old_status = None

            # Schedule message if this is a new injected patient or status changed to injected
            if is_created or old_status != 'injected':
                try:
                    # Format phone number for international use
                    phone = model.get('phone')
                    if phone:
                        if not phone.startswith('+'):
                            phone = '+' + phone
                        
                        # Get appropriate language
                        nationality = model.get('nationality', 'arab')
                        patient_name = model.get('name', '')
                        
                        # Schedule the follow-up message for 2 days later instead of sending immediately
                        from utils.whatsapp import schedule_injection_followup
                        
                        # Store patient ID as string since it might be a new record
                        patient_id = str(model.get('_id', 'pending'))
                        
                        # Schedule the message
                        message_id = schedule_injection_followup(
                            patient_id=patient_id,
                            phone=phone,
                            patient_name=patient_name,
                            nationality=nationality,
                            delay_days=2  # Schedule for 2 days later
                        )
                        
                        # We'll record the scheduled followup after the patient is saved
                        # in the after_model_change method, since we need the patient_id
                        model['_schedule_followup'] = True
                        model['_followup_phone'] = phone
                        model['_followup_message_id'] = message_id
                        
                except Exception as e:
                    logger.error(f"Error scheduling injection followup: {str(e)}")

    def after_model_change(self, form, model, is_created):
        """Run after the model has been saved to the database"""
        # Check if we need to create a scheduled followup record
        if model.get('_schedule_followup'):
            try:
                scheduled_date = datetime.utcnow() + timedelta(days=2)
                db.followups.insert_one({
                    'patient_id': model['_id'],
                    'patient_name': model.get('name', ''),
                    'status': 'scheduled',
                    'scheduled_date': scheduled_date,
                    'message_type': 'post_injection',
                    'phone': model.get('_followup_phone'),
                    'scheduled_message_id': model.get('_followup_message_id')
                })
                logger.info(f"Injection followup message scheduled for {model.get('_followup_phone')}")
            except Exception as e:
                logger.error(f"Error creating followup record: {str(e)}")

class FollowUpForm(form.Form):
    patient_id = fields.SelectField('المريض')
    notes = fields.TextAreaField('ملاحظات')
    next_appointment = fields.DateField('موعد المتابعة القادم')
    status = fields.SelectField('الحالة', choices=[
        ('pending', 'قيد الانتظار'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي')
    ])

    def __init__(self, *args, **kwargs):
        super(FollowUpForm, self).__init__(*args, **kwargs)
        # Get only injected patients
        patients = list(db.patients.find({'injection_status': 'injected'}))
        self.patient_id.choices = [(str(p['_id']), p['name']) for p in patients]

class FollowUpView(AdminModelView):
    column_list = ('patient_name', 'next_appointment', 'status')
    column_labels = {
        'patient_name': 'المريض',
        'next_appointment': 'موعد المتابعة',
        'status': 'الحالة',
        'notes': 'ملاحظات'
    }
    form = FollowUpForm

    column_formatters = {
        'next_appointment': lambda v, c, m, p: m['next_appointment'].strftime('%Y-%m-%d') if m.get('next_appointment') else ''
    }

    def on_model_change(self, form, model, is_created):
        # Handle patient name
        patient = db.patients.find_one({'_id': ObjectId(form.patient_id.data)})
        if patient:
            model['patient_name'] = patient['name']

        # Convert next_appointment date to datetime for MongoDB storage
        if isinstance(form.next_appointment.data, date):
            model['next_appointment'] = datetime.combine(form.next_appointment.data, datetime.min.time())
        elif isinstance(form.next_appointment.data, str):
            date_obj = datetime.strptime(form.next_appointment.data, '%Y-%m-%d')
            model['next_appointment'] = datetime.combine(date_obj.date(), datetime.min.time())

        # Add created_at timestamp for new records
        if is_created:
            model['created_at'] = datetime.utcnow()

            # Send follow-up message if it's a new follow-up
            if is_created:
                patient = db.patients.find_one({'_id': ObjectId(form.patient_id.data)})
                if patient:
                    # Schedule message to be sent
                    model['message_status'] = 'pending'
                    model['patient_nationality'] = patient.get('nationality', 'arab')
                    model['patient_phone'] = patient.get('phone')
                    
                    # Send immediate message
                    try:
                        send_followup_message(
                            phone=patient['phone'],
                            nationality=patient['nationality'],
                            next_appointment=model['next_appointment']
                        )
                        model['message_status'] = 'sent'
                    except Exception as e:
                        logger.error(f"Error sending follow-up message: {e}")
                        model['message_status'] = 'failed'

class PatientResponseView(BaseView):
    """View for patient responses to follow-ups"""
    @expose('/')
    def index(self):
        # Get only the FIRST response from each injected patient
        responses = list(db.followups.aggregate([
            {'$match': {'patient_response': {'$ne': None}}},  # Has a response
            {'$sort': {'response_date': 1}},  # Sort by date ascending to get earliest responses first
            {'$group': {
                '_id': '$patient_id',  # Group by patient ID
                'first_response': {'$first': '$$ROOT'}  # Keep only the first document in each group
            }},
            {'$replaceRoot': {'newRoot': '$first_response'}},  # Replace the grouped doc with the original
            {'$lookup': {
                'from': 'patients',
                'localField': 'patient_id',
                'foreignField': '_id',
                'as': 'patient'
            }},
            {'$unwind': '$patient'},
            {'$match': {'patient.injection_status': 'injected'}},  # Only injected patients
            {'$project': {
                'patient_name': '$patient.name',
                'patient_phone': '$patient.phone',
                'scheduled_date': 1,
                'response_date': 1,
                'patient_response': 1,
                'status': 1
            }},
            {'$sort': {'patient_name': 1}}  # Sort by patient name for better readability
        ]))
        
        # Format dates for display
        for response in responses:
            if 'scheduled_date' in response and response['scheduled_date']:
                response['scheduled_date_formatted'] = response['scheduled_date'].strftime('%Y-%m-%d')
            else:
                response['scheduled_date_formatted'] = 'N/A'
                
            if 'response_date' in response and response['response_date']:
                response['response_date_formatted'] = response['response_date'].strftime('%Y-%m-%d %H:%M')
            else:
                response['response_date_formatted'] = 'N/A'
        
        # Print for debugging
        print(f"Found {len(responses)} unique patient first responses")
        
        return self.render('admin/responses.html', responses=responses)

class MessageHistoryView(BaseView):
    """View for all WhatsApp messages"""
    @expose('/')
    def index(self):
        # Get recent messages
        messages = list(db.message_history.find().sort('timestamp', -1).limit(100))
        
        # Format dates for display
        for msg in messages:
            if 'timestamp' in msg and msg['timestamp']:
                msg['timestamp_formatted'] = msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                msg['timestamp_formatted'] = 'N/A'
        
        return self.render('admin/message_history.html', messages=messages)

class DashboardView(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        total_patients = db.patients.count_documents({})
        injected_patients = db.patients.count_documents({'injection_status': 'injected'})
        active_followups = db.followups.count_documents({'status': 'pending'})
        
        # Get recent patient responses
        recent_responses = list(db.followups.aggregate([
            {'$match': {'patient_response': {'$ne': None}}},
            {'$lookup': {
                'from': 'patients',
                'localField': 'patient_id',
                'foreignField': '_id',
                'as': 'patient'
            }},
            {'$unwind': '$patient'},
            {'$project': {
                'patient_name': '$patient.name',
                'response_date': 1,
                'patient_response': 1
            }},
            {'$sort': {'response_date': -1}},
            {'$limit': 5}
        ]))
        
        # Get upcoming followups
        upcoming_followups = list(db.followups.find(
            {'status': 'pending', 'scheduled_date': {'$gte': datetime.utcnow()}},
            {'patient_name': 1, 'scheduled_date': 1}
        ).sort('scheduled_date', 1).limit(5))
        
        return self.render('admin/index.html',
                          total_patients=total_patients,
                          injected_patients=injected_patients,
                          active_followups=active_followups,
                          recent_responses=recent_responses,
                          upcoming_followups=upcoming_followups)
