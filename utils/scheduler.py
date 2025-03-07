from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging
from pymongo import MongoClient
from .whatsapp import send_template_message

logger = logging.getLogger(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['dr_wasim_db']

def check_and_send_followups():
    """Check for pending follow-ups and send messages"""
    try:
        current_time = datetime.utcnow()
        query = {
            'status': 'pending',
            'message_sent': False,
            'scheduled_date': {'$lte': current_time}
        }

        pending_followups = db.followups.find(query)

        for followup in pending_followups:
            try:
                # Always use template for scheduled follow-ups
                send_template_message(
                    phone=followup['patient_phone'],
                    template_name='followup_check',
                    language=followup['patient_nationality'],
                    params={'patient_name': followup['patient_name']}
                )

                db.followups.update_one(
                    {'_id': followup['_id']},
                    {
                        '$set': {
                            'message_sent': True,
                            'sent_at': current_time,
                            'message_type': 'template'
                        }
                    }
                )

                logger.info(f"Sent template follow-up to {followup['patient_name']}")

            except Exception as e:
                logger.error(f"Error sending follow-up to {followup['patient_name']}: {str(e)}")

    except Exception as e:
        logger.error(f"Error in follow-up scheduler: {str(e)}")

def init_scheduler():
    """Initialize the scheduler"""
    scheduler = BackgroundScheduler()
    
    # Check for follow-ups every 5 minutes
    scheduler.add_job(
        check_and_send_followups,
        CronTrigger(minute='*/5'),
        id='followup_scheduler',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started")
    return scheduler
