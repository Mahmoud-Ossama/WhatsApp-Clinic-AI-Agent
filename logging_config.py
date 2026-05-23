"""
Logging configuration for the DR_WASIM3 application.
Enhanced logging setup to help diagnose conversation flow issues.
Compatible with both local and App Engine environments.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def is_running_on_app_engine():
    """Check if the application is running on Google App Engine"""
    return os.environ.get('GAE_ENV', '').startswith('standard') or \
           os.environ.get('GOOGLE_CLOUD_PROJECT') is not None

def setup_logging(app_name="dr_wasim", log_level=logging.INFO):
    """
    Configure application-wide logging
    
    Args:
        app_name (str): Name of the application for log file naming
        log_level (int): Logging level (e.g., logging.DEBUG, logging.INFO)
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    standard_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # Console handler (for all environments)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(standard_formatter)
    root_logger.addHandler(console)
    
    # Check if we're running on App Engine
    running_on_app_engine = is_running_on_app_engine()
    
    # Set up file handlers only if not on App Engine or if we can use /tmp
    if not running_on_app_engine:
        try:
            # Create logs directory if it doesn't exist
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # File handler for general logs (rotating, max 5MB per file, keep 10 files)
            general_log = RotatingFileHandler(
                os.path.join(log_dir, f"{app_name}.log"),
                maxBytes=5*1024*1024,
                backupCount=10
            )
            general_log.setLevel(log_level)
            general_log.setFormatter(detailed_formatter)
            root_logger.addHandler(general_log)
            
            # Create a separate log file specifically for conversation flows
            flow_log = RotatingFileHandler(
                os.path.join(log_dir, f"{app_name}_flows.log"),
                maxBytes=5*1024*1024,
                backupCount=10
            )
            flow_log.setLevel(logging.DEBUG)  # Always DEBUG level for flows
            flow_log.setFormatter(detailed_formatter)
            
            # Add this handler only to the flow loggers
            flow_loggers = [
                logging.getLogger("custom_nlp.flow_manager"),
                logging.getLogger("custom_nlp.conversation_flows"),
                logging.getLogger("utils.store_conversation_state")
            ]
            
            for logger in flow_loggers:
                logger.setLevel(logging.DEBUG)
                logger.addHandler(flow_log)
                # Set propagate to False to avoid duplicate logs in the root logger
                logger.propagate = False
            
            # Create a separate error log file
            error_log = RotatingFileHandler(
                os.path.join(log_dir, f"{app_name}_errors.log"),
                maxBytes=5*1024*1024,
                backupCount=10
            )
            error_log.setLevel(logging.ERROR)
            error_log.setFormatter(detailed_formatter)
            root_logger.addHandler(error_log)
            
        except (OSError, IOError) as e:
            # If we can't create log files, fall back to console logging
            logging.warning(f"Could not set up file logging: {str(e)}. Using console logging only.")
    else:
        # App Engine environment - try to use the /tmp directory for logs
        try:
            tmp_log_file = os.path.join('/tmp', f"{app_name}.log")
            file_handler = logging.FileHandler(tmp_log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)
            logging.info(f"Logging to temporary file: {tmp_log_file}")
        except (OSError, IOError) as e:
            logging.warning(f"Could not set up temporary file logging: {str(e)}. Using console logging only.")
    
    # Set specific loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Log the environment information
    if running_on_app_engine:
        logging.info("Running on Google App Engine environment")
    else:
        logging.info("Running in local environment")
    
    return root_logger
