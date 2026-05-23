"""
Scheduled task runner for processing scheduled messages
This script should be run by a cron job or scheduler at regular intervals 
(e.g., every 5-15 minutes) when running locally, or can be used for manual tests.
On App Engine, the tasks.py endpoints will be used instead.
"""
import sys
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='scheduler.log'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main function to process scheduled tasks"""
    start_time = datetime.now()
    logger.info(f"Starting scheduled tasks at {start_time}")
    
    try:
        # Import the message processing function
        from utils.whatsapp import process_scheduled_messages
        
        # Process scheduled messages
        sent_count = process_scheduled_messages()
        
        logger.info(f"Successfully processed {sent_count} scheduled messages")
        
    except Exception as e:
        logger.error(f"Error in scheduler: {str(e)}")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Scheduled tasks completed in {duration:.2f} seconds")


if __name__ == "__main__":
    main()
