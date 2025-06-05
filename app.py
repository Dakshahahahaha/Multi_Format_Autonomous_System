import streamlit as st
import os
import json
from utils import logger, generate_transaction_id, safe_json_dump, get_current_timestamp
from config import DATA_DIR, OUTPUT_DIR, DB_PATH
from document_loader import DocumentLoader
from ocr_processor import OCRProcessor
from classifier import LLMClassifier
from router import DocumentRouter
from my_context import ProcessingContextManager
from payment_processor_mock import PaymentProcessorMock

doc_loader = DocumentLoader()
ocr_processor = OCRProcessor()

llm_classifier = None
try:
    llm_classifier = LLMClassifier()
except ImportError:
    st.error("Error: 'google-generativeai' library not installed. Please run 'pip install google-generativeai'.")
except ValueError as e:
    st.error(f"Error initializing LLMClassifier: {e}. Please ensure GEMINI_API_KEY is set in your .env file.")
except Exception as e:
    st.error(f"An unexpected error occurred during LLMClassifier initialization: {e}")


doc_router = DocumentRouter()
my_context_manager = ProcessingContextManager()
payment_processor = PaymentProcessorMock()


def process_document(file_path, transaction_id, sender_info="DemoUser"):
    st.session_state.current_status = "Processing started..."
    st.session_state.logs = []
    current_errors = []

    def log_step(message, level="info"):
        timestamp = get_current_timestamp()
        log_entry = {"message": message, "timestamp": timestamp, "level": level}
        st.session_state.logs.append(log_entry)
        logger.info(message)
        my_context_manager.update_context(transaction_id, intermediate_steps=[log_entry])


    log_step(f"Starting processing for {os.path.basename(file_path)} (ID: {transaction_id})")
    my_context_manager.create_context(transaction_id, sender=sender_info, original_filepath=file_path)


    log_step("Detecting document format and loading content...")
    format_type, loaded_content, load_error = doc_loader.load_document(file_path)
    if load_error:
        log_step(f"Document loading failed: {load_error}", "error")
        current_errors.append(f"Load Error: {load_error}")
        my_context_manager.update_context(transaction_id, errors=current_errors)
        return None, None, current_errors

    original_raw_content = loaded_content
    my_context_manager.update_context(transaction_id, original_content=original_raw_content)

    document_text_content = ""
    if format_type == "pdf":
        log_step("Detected PDF. Performing OCR or direct text extraction...")
        ocr_text, ocr_error = ocr_processor.process_pdf(loaded_content)
        if ocr_error:
            log_step(f"OCR/PDF text extraction failed: {ocr_error}", "error")
            current_errors.append(f"OCR Error: {ocr_error}")
            document_text_content = ""
        else:
            document_text_content = ocr_text
            log_step(f"OCR/PDF text extraction completed. Text length: {len(document_text_content)}")
    elif format_type in ["json", "text"]:
        document_text_content = loaded_content
        log_step(f"Loaded non-PDF content. Text length: {len(document_text_content)}")
    else:
        log_step(f"Unsupported document format: {format_type}", "error")
        current_errors.append(f"Unsupported Format: {format_type}")
        my_context_manager.update_context(transaction_id, errors=current_errors)
        return None, None, current_errors

    if not document_text_content:
        log_step("No extractable text content available for classification or extraction.", "error")
        current_errors.append("No text content for processing.")
        my_context_manager.update_context(transaction_id, errors=current_errors)
        return None, None, current_errors


    classification_output = {"purpose": "Unknown", "confidence": 0.0}
    if llm_classifier:
        log_step("Classifying document purpose using LLM...")
        try:
            classification_output = llm_classifier.classify_purpose(document_text_content)
            log_step(f"Document classified as: {classification_output['purpose']} (Confidence: {classification_output['confidence']:.2f})")
            my_context_manager.update_context(transaction_id, classification_output=classification_output)
        except Exception as e:
            log_step(f"LLM classification failed: {e}", "error")
            current_errors.append(f"Classification Error: {e}")
            classification_output = {"purpose": "Unknown", "confidence": 0.0}
            my_context_manager.update_context(transaction_id, errors=current_errors)
    else:
        log_step("LLM classifier not initialized. Skipping purpose classification.", "warning")
        current_errors.append("LLM classifier not available.")


    extracted_data = {}
    extraction_confidence = 0.0
    extraction_error = None
    if classification_output["purpose"] != "Unknown":
        log_step(f"Routing to {classification_output['purpose']} extraction agent...")
        extracted_data, extraction_confidence, extraction_error = doc_router.route_and_extract(
            classification_output["purpose"],
            document_text_content
        )
        if extraction_error:
            log_step(f"Extraction by agent failed: {extraction_error}", "error")
            current_errors.append(f"Extraction Error: {extraction_error}")
        else:
            log_step(f"Extraction completed with confidence: {extraction_confidence:.2f}")
            my_context_manager.update_context(transaction_id, extracted_fields=extracted_data)
    else:
        log_step("Document purpose is 'Unknown'. Skipping specialized extraction.", "warning")
        current_errors.append("Document purpose unknown, no specialized extraction performed.")

    payment_status = None
    if classification_output["purpose"] == "Invoice" and extracted_data.get("invoice_number") and extracted_data.get("total_amount"):
        log_step("Detected Invoice with extracted data. Triggering mock payment processing...")
        payment_status = payment_processor.process_invoice_payment(
            extracted_data["invoice_number"],
            extracted_data["total_amount"],
            extracted_data.get("currency", "USD")
        )
        log_step(f"Mock Payment Status: {payment_status['status']}", "info" if payment_status['status'] == 'success' else "warning")
        my_context_manager.update_context(transaction_id, intermediate_steps=[
            {"step": "Mock Payment Processed", "details": payment_status, "timestamp": get_current_timestamp()}
        ])

    if current_errors:
        my_context_manager.update_context(transaction_id, errors=current_errors)
    else:
        my_context_manager.update_context(transaction_id, errors=[])

    st.session_state.current_status = "Processing complete."
    return document_text_content, classification_output, extracted_data, payment_status, current_errors

st.set_page_config(layout="wide", page_title="Intelligent Document Processor")

st.title("📄 Intelligent Document Processor")
st.markdown("Automated classification, extraction, and routing for diverse document types.")

st.sidebar.header("Try with Example Files")
example_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(('.pdf', '.json', '.txt'))]
example_files.insert(0, "Upload your own...")

selected_example = st.sidebar.selectbox("Choose an example document:", example_files)

uploaded_file = st.sidebar.file_uploader("Or upload a document", type=["pdf", "json", "txt"])

document_to_process = None
file_name = None

if selected_example != "Upload your own...":
    document_to_process = os.path.join(DATA_DIR, selected_example)
    file_name = selected_example
elif uploaded_file is not None:
    temp_file_path = os.path.join(DATA_DIR, uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    document_to_process = temp_file_path
    file_name = uploaded_file.name
else:
    st.info("Please select an example document or upload your own to start processing.")

process_button = st.sidebar.button("Process Document")

if 'current_status' not in st.session_state:
    st.session_state.current_status = "Awaiting document..."
if 'logs' not in st.session_state:
    st.session_state.logs = []

st.header("Processing Workflow")
st.text_area("Live Log", value="\n".join([f"[{e['timestamp']}] {e['level'].upper()}: {e['message']}" for e in st.session_state.logs]), height=300)
st.write(f"**Current Status:** {st.session_state.current_status}")

if process_button and document_to_process:
    if llm_classifier is None:
        st.error("Cannot process: LLM classifier not initialized. Check API keys.")
    else:
        st.session_state.logs = []
        transaction_id = generate_transaction_id()
        st.session_state.current_processing_id = transaction_id
        
        st.session_state.processed_document_text = ""
        st.session_state.classification_result = {}
        st.session_state.extracted_data = {}
        st.session_state.payment_status = {}
        st.session_state.errors = []

        with st.spinner("Processing document... This may take a moment due to LLM calls and OCR."):
            processed_text, classification, extracted, payment, errors = process_document(
                document_to_process, transaction_id, sender_info=f"Streamlit User ({file_name})"
            )
            st.session_state.processed_document_text = processed_text
            st.session_state.classification_result = classification
            st.session_state.extracted_data = extracted
            st.session_state.payment_status = payment
            st.session_state.errors = errors
        st.rerun()

if st.session_state.get('processed_document_text'):
    st.subheader("Processing Results")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Document Text (after OCR if PDF)")
        st.code(st.session_state.processed_document_text[:1500] + "..." if len(st.session_state.processed_document_text) > 1500 else st.session_state.processed_document_text, language='text')

        st.markdown("#### Classification Output")
        st.json(st.session_state.classification_result)

        st.markdown("#### Extracted Data")
        st.json(st.session_state.extracted_data)

    with col2:
        st.markdown("#### Traceability (Context Log)")
        my_current_context = my_context_manager.get_context(st.session_state.current_processing_id)
        if my_current_context:
            st.json(my_current_context)
        else:
            st.info("Context not yet available or error retrieving.")

        if st.session_state.payment_status:
            st.markdown("#### Downstream Chaining (Mock Payment)")
            st.json(st.session_state.payment_status)

        if st.session_state.errors:
            st.markdown("#### Errors/Warnings")
            for err in st.session_state.errors:
                st.error(err)
else:
    st.info("Upload a document and click 'Process Document' to see results.")

st.markdown("---")
st.subheader("All Processed Documents (Historical Context)")
all_contexts = my_context_manager.get_all_contexts()
if all_contexts:
    selected_context_id = st.selectbox(
        "Select a past transaction ID to view its full context:",
        [ctx['transaction_id'] for ctx in all_contexts]
    )
    if selected_context_id:
        selected_context = next((ctx for ctx in all_contexts if ctx['transaction_id'] == selected_context_id), None)
        if selected_context:
            st.json(selected_context)
else:
    st.info("No past processing history found.")