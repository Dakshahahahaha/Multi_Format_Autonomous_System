from utils import logger
from extraction_agents.invoice_agent import InvoiceExtractionAgent
from extraction_agents.email_agent import EmailExtractionAgent
from config import GEMINI_API_KEY, GEMINI_MODEL_NAME


class DocumentRouter:
    def __init__(self):
        logger.info("Initializing DocumentRouter...")
        self.extraction_agents = {
            "Invoice": InvoiceExtractionAgent(),
            "Email": EmailExtractionAgent(),
        }
        logger.info(f"Initialized Document Router with agents for: {list(self.extraction_agents.keys())}")

    def route_and_extract(self, document_purpose, document_content):
        agent = self.extraction_agents.get(document_purpose)

        if agent:
            logger.info(f"Routing document to {document_purpose} Extraction Agent.")
            try:
                extracted_data, confidence = agent.extract_data(document_content)
                return extracted_data, confidence, None
            except Exception as e:
                logger.error(f"Error during extraction by {document_purpose} Agent: {e}")
                return {}, 0.0, f"Extraction failed for {document_purpose}: {e}"
        else:
            logger.warning(f"No specialized extraction agent found for purpose: {document_purpose}. Returning empty data.")
            return {}, 0.0, f"No agent for {document_purpose}"

if __name__ == "__main__":
    router = DocumentRouter()

    invoice_text = """
    Invoice No: INV-XYZ
    Total Due: $500.00
    """
    email_text = """
    Subject: Support Request - Order ID: 123
    From: test@example.com
    Body of email...
    """
    contract_text = """
    This is a dummy contract text.
    """

    print("\n--- Router Test: Invoice ---")
    extracted_invoice, conf_invoice, err_invoice = router.route_and_extract("Invoice", invoice_text)
    print(f"Extracted Invoice: {extracted_invoice}, Confidence: {conf_invoice:.2f}, Error: {err_invoice}")

    print("\n--- Router Test: Email ---")
    extracted_email, conf_email, err_email = router.route_and_extract("Email", email_text)
    print(f"Extracted Email: {extracted_email}, Confidence: {conf_email:.2f}, Error: {err_email}")

    print("\n--- Router Test: Unknown Type ---")
    extracted_unknown, conf_unknown, err_unknown = router.route_and_extract("UnknownDocType", contract_text)
    print(f"Extracted Unknown: {extracted_unknown}, Confidence: {conf_unknown:.2f}, Error: {err_unknown}")

    print("\n--- Router Test: Other (no specific agent, but LLM might classify as such) ---")
    extracted_other, conf_other, err_other = router.route_and_extract("Other", contract_text)
    print(f"Extracted Other: {extracted_other}, Confidence: {conf_other:.2f}, Error: {err_other}")