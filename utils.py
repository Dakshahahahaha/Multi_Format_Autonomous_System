import uuid
import logging
import json
from datetime import datetime
from config import LOG_FILE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_transaction_id():
    """Generates a unique transactions ID."""
    return str(uuid.uuid4())

def safe_json_dump(data):
    """Safely dump data to a JSON string."""
    try:
        return json.dumps(data, indent=2, default=str)
    except TypeError as e:
        logger.error(f"Failed to dump data to JSON: {e}")
        return json.dumps({"error": f"failed to serialize: {str(e)}"})
    
def get_current_timestamp():
    """returns the current UTC  timestamp."""
    return datetime.utcnow().isoformat()