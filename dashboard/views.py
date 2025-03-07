from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.pymongo import ModelView
from flask_admin.form import rules
from flask_login import current_user, login_required
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
        ('israeli', 'صهيوني')
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
    
    column_formatters = {
        'medical_date': lambda v, c, m, p: m['medical_date'].strftime('%Y-%m-%d') if m.get('medical_date') else '',
        'created_at': lambda v, c, m, p: m['created_at'].strftime('%Y-%m-%d') if m.get('created_at') else ''
    }

    def on_model_change(self, form, model, is_created):
        # Handle dates
        if isinstance(form.medical_date.data, date):
            model['medical_date'] = datetime.combine(form.medical_date.data, datetime.min.time())
        elif isinstance(form.medical_date.data, str):
            date_obj = datetime.strptime(form.medical_date.data, '%Y-%m-%d')
            model['medical_date'] = datetime.combine(date_obj.date(), datetime.min.time())
        
        # Add created_at timestamp for new records
        if is_created:
            model['created_at'] = datetime.utcnow()
            
        # Send initial message if patient is marked as injected
        if form.injection_status.data == 'injected':
            old_status = None
            if not is_created:
                # Get the old record to check if status changed
                old_record = self.coll.find_one({'_id': model.get('_id')})
                old_status = old_record.get('injection_status') if old_record else None

            # Send message if this is a new injected patient or status changed to injected
            if is_created or old_status != 'injected':
                try:
                    # Send template message instead of regular message
                    from utils.whatsapp import send_template_message
                    send_template_message(
                        phone=form.phone.data,
                        template_name="followup_status_check",
                        language=form.nationality.data
                    )
                    model['initial_message_sent'] = True

                    # Schedule follow-up in 2 days
                    followup_date = datetime.now() + timedelta(days=2)
                    followup_id = db.followups.insert_one({
                        'patient_id': model['_id'],
                        'patient_name': model['name'],
                        'patient_phone': form.phone.data,
                        'patient_nationality': form.nationality.data,
                        'scheduled_date': followup_date,
                        'status': 'pending',
                        'message_sent': False,
                        'created_at': datetime.utcnow()
                    }).inserted_id
                    
                    model['followup_id'] = followup_id
                    model['followup_scheduled'] = True
                    logger.info(f"Template message sent successfully to new injected patient: {form.phone.data}")

                except Exception as e:
                    logger.error(f"Error handling new injection: {e}")
                    model['initial_message_sent'] = False
                    model['followup_scheduled'] = False

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

class DashboardView(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        total_patients = db.patients.count_documents({})
        injected_patients = db.patients.count_documents({'injection_status': 'injected'})
        active_followups = db.followups.count_documents({'status': 'pending'})
        
        return self.render('admin/index.html',
                          total_patients=total_patients,
                          injected_patients=injected_patients,
                          active_followups=active_followups)
