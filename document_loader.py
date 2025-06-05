import os
import json
from utils import logger

class DocumentLoader:
    def __init__(self):
        pass

    def _is_pdf(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                return header == b'%PDF'
        except Exception as e:
            logger.error(f"Error checking PDF header for {file_path}: {e}")
            return False

    def _is_json(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False
        except Exception as e:
            logger.error(f"Error checking JSON content for {file_path}: {e}")
            return False

    def load_document(self, file_path):
        if not os.path.exists(file_path):
            return "unknown", None, f"File not found: {file_path}"

        try:
            if self._is_pdf(file_path):
                logger.info(f"Detected PDF format for: {file_path}")
                return "pdf", file_path, None
            elif self._is_json(file_path):
                logger.info(f"Detected JSON format for: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return "json", content, None
            else:
                logger.info(f"Detected Text format for: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return "text", content, None
        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {e}")
            return "unknown", None, f"Failed to load document: {e}"

if __name__ == "__main__":
    loader = DocumentLoader()

    with open("test_doc.pdf", "wb") as f:
        f.write(b"%PDF-1.4\n%DUMMY PDF")
    with open("test_doc.json", "w") as f:
        f.write('{"name": "test", "type": "json"}')
    with open("test_doc.txt", "w") as f:
        f.write("This is a plain text document.")
    with open("non_existent_file.xyz", "w") as f:
        pass

    format_type, content, error = loader.load_document("test_doc.pdf")
    print(f"PDF Test: Format={format_type}, Content (path for PDF)='{content}', Error='{error}'")

    format_type, content, error = loader.load_document("test_doc.json")
    print(f"JSON Test: Format={format_type}, Content='{content}', Error='{error}'")

    format_type, content, error = loader.load_document("test_doc.txt")
    print(f"Text Test: Format={format_type}, Content='{content}', Error='{error}'")

    format_type, content, error = loader.load_document("non_existent_file.xyz")
    print(f"Unknown Test: Format={format_type}, Content='{content}', Error='{error}'")

    format_type, content, error = loader.load_document("no_such_file.pdf")
    print(f"Missing File Test: Format={format_type}, Content='{content}', Error='{error}'")

    os.remove("test_doc.pdf")
    os.remove("test_doc.json")
    os.remove("test_doc.txt")
    os.remove("non_existent_file.xyz")