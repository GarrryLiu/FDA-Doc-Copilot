import logging
import os
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """
    Set up logging configuration
    
    Args:
        log_level: The logging level (default: INFO)
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/fda_copilot_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    
    # Return the logger
    return logging.getLogger('fda_copilot')
