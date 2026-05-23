"""
Task handlers for scheduled jobs on Google Cloud App Engine
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint for task routes
tasks_blueprint = Blueprint('tasks', __name__, url_prefix='/tasks')

@tasks_blueprint.route('/process-scheduled-messages', methods=['GET'])
def process_scheduled_messages_task():
    """Process all scheduled messages that are due to be sent"""
    # Verify the request came from App Engine scheduler
    if not is_app_engine_cron(request):
        return jsonify({"error": "Unauthorized"}), 403
    
    start_time = datetime.now()
    logger.info(f"Starting scheduled message processing at {start_time}")
    
    try:
        # Import and call the message processing function
        from utils.whatsapp import process_scheduled_messages
        sent_count = process_scheduled_messages()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result = {
            "success": True,
            "messages_processed": sent_count,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Processed {sent_count} scheduled messages in {duration:.2f} seconds")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error processing scheduled messages: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@tasks_blueprint.route('/daily-processing-check', methods=['GET'])
def daily_processing_check():
    """Daily verification that message processing is working"""
    if not is_app_engine_cron(request):
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        from dashboard.models import db
        
        # Check for any failed scheduled messages in the last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        failed_count = db.scheduled_messages.count_documents({
            'status': 'failed',
            'scheduled_date': {'$gte': yesterday}
        })
        
        # Check for scheduled messages that should have been sent but weren't
        pending_old = db.scheduled_messages.count_documents({
            'status': 'scheduled',
            'scheduled_date': {'$lt': yesterday}
        })
        
        result = {
            "success": True,
            "failed_messages_24h": failed_count,
            "pending_old_messages": pending_old,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Daily check: {failed_count} failed messages, {pending_old} old pending messages")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in daily processing check: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def is_app_engine_cron(request):
    """Verify that the request comes from App Engine cron service"""
    return request.headers.get('X-Appengine-Cron', '') == 'true' or \
           os.environ.get('FLASK_ENV') == 'development'
