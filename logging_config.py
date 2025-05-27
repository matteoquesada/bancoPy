import logging
import os

def setup_logging(log_file_name='banco_app.log', log_level=logging.INFO):
    """Sets up basic file logging."""
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    log_file_path = os.path.join(logs_dir, log_file_name)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler() # Also log to console
        ]
    )
    logging.info("Logging configured.")