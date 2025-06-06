This project is a multi format autonomous document processing system designed to classify various document types(e.g., Invoice, Emails, Contracts) and extract relevant information using large language models(LLM'S) and OCR capabilities. 
It has a streamlit based user interface for easy interaction and a SQLite database for managing processing texts.

Some of its features are:
1.Document Loading
2.Optical Character Recognition (OCR)
3.LLM-based Classification
4.Intelligent Data Extraction
5.Streamlit UI

The tech-stack used was:
1.Python
2.Google gemini API
3.PyMuPDF
4.Pillow
5.Pytesseract
6.SQLite
7.Streamlit
8.Docker
9.Logging module

Architecture:
The user uploads a document via the streamlit interface app.py, this document is identfied by the document loader on the basis of file type.If it's a PDF, its path is passed. For JSON/TXT, the content is read directly.
If pdf is detected the OCR processor attemps text.It first tries direct text extraction (for searchable PDFs) and falls back to image-based OCR using Tesseract if minimal text is found. The extracted text then becomes the `document_content`.
The extracted `document_content` (or direct content for JSON/TXT) is sent to the `LLMClassifier` (`llm_classifier.py`). This component uses Google's Gemini LLM to determine the primary purpose of the document (e.g., "Invoice", "Email", "Other").
Based on the classified purpose, the `DocumentRouter` (`document_router.py`) directs the `document_content` to the appropriate specialized extraction agent.
Each agent (e.g., `InvoiceExtractionAgent`, `EmailExtractionAgent`) is designed to extract specific, structured data relevant to its document type, typically by prompting the LLM.
Throughout this process, the `ProcessingContextManager` (`processing_context_manager.py`) records all steps, inputs, outputs, and any errors to a SQLite database, providing a complete audit trail and history.
Finally, all extracted data and processing status are displayed back to the user in the Streamlit UI and persisted in the database.

Agent Logic:
The "agents" in this system primarily refer to the `LLMClassifier` and the specialized `ExtractionAgents`. They leverage Large Language Models to perform their tasks.
1. `LLMClassifier` (`llm_classifier.py`)
   This agent is responsible for determining the overall purpose of a document.
   It initializes a Google Gemini `GenerativeModel` client using `GEMINI_API_KEY` and `GEMINI_MODEL_NAME` from `config.py`.
   It defines a fixed list of `document_types` it can classify into (e.g., "Invoice","Email","Other").

2. Specialized Extraction Agents (e.g., `InvoiceExtractionAgent`, `EmailExtractionAgent`)
   These agents reside in the `extraction_agents/` directory and are designed for fine-grained data extraction based on the document's classified purpose.
   Invoice Extraction Agent
   Fields to Extract:`invoice_number`, `invoice_date`, `total_amount`, `currency`, `vendor_name`, `customer_name`.
   Prompting Strategy: Focuses on keywords like "Invoice No:", "Total Due:", "Date:", and standard invoice structures to guide the LLM. It specifically requests the output in JSON format with these keys.
   Post-processing:Converts `total_amount` to a float if possible and handles missing fields gracefully.

3.Email Extraction Agent
  Fields to Extract:`sender_email`, `recipient_email`, `subject`, `date_sent`, `body_summary`.
  Prompting Strategy:Targets email headers (From, To, Subject, Date) and requests a concise summary of the email body. It also enforces JSON output.

   
