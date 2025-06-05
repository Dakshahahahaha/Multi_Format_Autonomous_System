import sqlite3
import json
import uuid
from utils import logger, get_current_timestamp
from config import DB_PATH
import os

def generate_transaction_id():
    return str(uuid.uuid4())

class ProcessingContextManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._ensure_db_directory_exists()
        self.conn = self._connect_db()
        self._create_table()

    def _ensure_db_directory_exists(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")

    def _connect_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def _create_table(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_contexts (
                    transaction_id TEXT PRIMARY KEY,
                    sender TEXT,
                    original_filepath TEXT,
                    original_content TEXT,
                    classification_output TEXT,
                    extracted_fields TEXT,
                    intermediate_steps TEXT,
                    errors TEXT,
                    timestamp TEXT
                )
            """)
            self.conn.commit()
            logger.info("Processing_contexts table ensured.")
        except sqlite3.Error as e:
            logger.error(f"Error creating table: {e}")
            raise

    def create_context(self, transaction_id, sender, original_filepath, original_content=None):
        timestamp = get_current_timestamp()
        try:
            self.conn.execute("""
                INSERT INTO processing_contexts (
                    transaction_id, sender, original_filepath, original_content, timestamp,
                    classification_output, extracted_fields, intermediate_steps, errors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_id,
                sender,
                original_filepath,
                original_content,
                timestamp,
                json.dumps({}),
                json.dumps({}),
                json.dumps([]),
                json.dumps([])
            ))
            self.conn.commit()
            logger.info(f"Context created for transaction ID: {transaction_id}")
        except sqlite3.IntegrityError:
            logger.warning(f"Context for transaction ID {transaction_id} already exists. Skipping creation.")
        except sqlite3.Error as e:
            logger.error(f"Error creating context: {e}")
            raise

    def update_context(self, transaction_id, **kwargs):
        cursor = self.conn.execute("SELECT * FROM processing_contexts WHERE transaction_id=?", (transaction_id,))
        existing_row = cursor.fetchone()
        
        if not existing_row:
            logger.warning(f"Attempted to update non-existent context for transaction ID: {transaction_id}")
            return

        existing_context = dict(existing_row)

        update_fields = []
        update_values = []

        for key, value in kwargs.items():
            if key in ['classification_output', 'extracted_fields']:
                update_fields.append(f"{key}=?")
                update_values.append(json.dumps(value))
            elif key in ['intermediate_steps', 'errors']:
                existing_list_json = existing_context.get(key)
                
                existing_list = []
                if existing_list_json:
                    try:
                        existing_list = json.loads(existing_list_json)
                        if not isinstance(existing_list, list):
                            existing_list = []
                            logger.warning(f"Context for {transaction_id}, key '{key}' was not a list after JSON load. Resetting.")
                    except (json.JSONDecodeError, TypeError):
                        logger.warning(f"Context for {transaction_id}, key '{key}' was not a valid JSON string. Treating as empty list for appending.")
                        existing_list = []
                
                if isinstance(value, list):
                    existing_list.extend(value)
                else:
                    existing_list.append(value)

                update_fields.append(f"{key}=?")
                update_values.append(json.dumps(existing_list))
            else:
                update_fields.append(f"{key}=?")
                update_values.append(value)

        if update_fields:
            sql = f"UPDATE processing_contexts SET {', '.join(update_fields)} WHERE transaction_id=?"
            update_values.append(transaction_id)
            try:
                self.conn.execute(sql, tuple(update_values))
                self.conn.commit()
                logger.info(f"Context updated for transaction ID: {transaction_id}")
            except sqlite3.Error as e:
                logger.error(f"Error updating context for {transaction_id}: {e}")
        else:
            logger.warning(f"No fields to update for transaction ID: {transaction_id}")

    def get_context(self, transaction_id):
        cursor = self.conn.execute("SELECT * FROM processing_contexts WHERE transaction_id=?", (transaction_id,))
        row = cursor.fetchone()
        if row:
            context_dict = dict(row)

            for key in ['classification_output', 'extracted_fields', 'intermediate_steps', 'errors']:
                if key in context_dict and isinstance(context_dict[key], str):
                    try:
                        context_dict[key] = json.loads(context_dict[key])
                    except (json.JSONDecodeError, TypeError):
                        logger.error(f"Failed to decode JSON for key '{key}' in transaction {transaction_id}. Data might be corrupted.")
                        context_dict[key] = {} if key in ['classification_output', 'extracted_fields'] else []
            return context_dict
        return None

    def get_all_contexts(self):
        cursor = self.conn.execute("SELECT * FROM processing_contexts ORDER BY timestamp DESC")
        all_contexts = []
        for row in cursor.fetchall():
            context_dict = dict(row)
            for key in ['classification_output', 'extracted_fields', 'intermediate_steps', 'errors']:
                if key in context_dict and isinstance(context_dict[key], str):
                    try:
                        context_dict[key] = json.loads(context_dict[key])
                    except (json.JSONDecodeError, TypeError):
                        logger.error(f"Failed to decode JSON for key '{key}' in context list for transaction {context_dict.get('transaction_id', 'N/A')}. Data might be corrupted.")
                        context_dict[key] = {} if key in ['classification_output', 'extracted_fields'] else []
            all_contexts.append(context_dict)
        return all_contexts

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    test_db_path = "test_context.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"Removed existing {test_db_path}")

    manager = ProcessingContextManager(db_path=test_db_path)

    test_id = generate_transaction_id()
    sender_info = "TestUser"
    original_file = "test_doc.pdf"
    original_content_str = "This is the content of the test document."

    print(f"\n--- Creating context for {test_id} ---")
    manager.create_context(test_id, sender_info, original_file, original_content_str)
    retrieved_context = manager.get_context(test_id)
    print(f"Initial context: {retrieved_context}")

    print("\n--- Updating classification and extracted fields ---")
    classification = {"purpose": "Invoice", "confidence": 0.95}
    extracted = {"invoice_number": "INV-2024-001", "total_amount": 100.50}
    manager.update_context(test_id, classification_output=classification, extracted_fields=extracted)
    retrieved_context = manager.get_context(test_id)
    print(f"Updated context: {retrieved_context}")
    print(f"Classification type: {type(retrieved_context['classification_output'])}")
    print(f"Extracted fields type: {type(retrieved_context['extracted_fields'])}")


    print("\n--- Adding intermediate steps ---")
    manager.update_context(test_id, intermediate_steps=[{"step": "OCR Completed", "status": "success"}])
    manager.update_context(test_id, intermediate_steps=[{"step": "Classification Done", "status": "success"}])
    retrieved_context = manager.get_context(test_id)
    print(f"Context with steps: {retrieved_context['intermediate_steps']}")
    print(f"Intermediate steps type: {type(retrieved_context['intermediate_steps'])}")


    print("\n--- Adding an error ---")
    manager.update_context(test_id, errors=["Failed to process image.", "LLM call timeout."])
    retrieved_context = manager.get_context(test_id)
    print(f"Context with errors: {retrieved_context['errors']}")
    print(f"Errors type: {type(retrieved_context['errors'])}")


    print("\n--- Testing get_all_contexts ---")
    all_contexts = manager.get_all_contexts()
    for ctx in all_contexts:
        print(f"  - {ctx['transaction_id']} (Purpose: {ctx['classification_output'].get('purpose') if ctx['classification_output'] else 'N/A'})")

    print("\n--- Testing update on a new field (if applicable) ---")
    new_id = generate_transaction_id()
    manager.create_context(new_id, "New User", "new_file.txt", "Some new content")
    manager.update_context(new_id, classification_output={"purpose": "Receipt", "confidence": 0.8})
    retrieved_new_context = manager.get_context(new_id)
    print(f"New context: {retrieved_new_context}")


    manager.close()
    print("\nDatabase operations completed and connection closed.")