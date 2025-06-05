import os
import dotenv 
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"

TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
DB_PATH = "context.db"

LOGS_DIR = "logs"
DATA_DIR = "data"
OUTPUT_DIR = "output"

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOGS_DIR, "system.log")
