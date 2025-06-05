import os
from utils import logger
from config import (
    GEMINI_API_KEY, GEMINI_MODEL_NAME
)

try:
    import google.generativeai as genai
    logger.info("Google Generative AI client imported.")
except ImportError:
    genai = None
    logger.warning("Google Generative AI library not found. Please run 'pip install google-generativeai'")


class LLMClassifier:
    def __init__(self):
        self.llm_provider = "gemini"
        self.client = None
        self.model_name = None

        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in .env or environment variables.")
        if genai:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model_name = GEMINI_MODEL_NAME
            self.client = genai.GenerativeModel(self.model_name)
            logger.info(f"Initialized Gemini classifier with model: {self.model_name}")
        else:
            raise ImportError("Google Generative AI library is not installed. Please run 'pip install google-generativeai'")

        self.document_types = ["Invoice", "Contract", "Email", "Order Confirmation", "Shipping Label", "Resume", "Other"]

    def _get_gemini_response(self, prompt):
        try:
            response = self.client.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return None

    def classify_purpose(self, document_content):
        if not document_content:
            logger.warning("Document content is empty for classification.")
            return {"purpose": "Unknown", "confidence": 0.0}

        prompt = f"""
        Analyze the following document content and classify its primary purpose.
        Choose one of the following categories: {', '.join(self.document_types)}.
        If the document does not clearly fit any of these categories, classify it as 'Other'.

        Return ONLY the chosen category name, with no additional text or explanation.

        Document Content:
        ---
        {document_content[:2000]}
        ---
        """
        logger.info(f"Sending classification prompt to {self.llm_provider}...")

        llm_output = None
        llm_output = self._get_gemini_response(prompt)

        if llm_output:
            cleaned_output = llm_output.replace('"', '').replace('.', '').strip()
            matched_purpose = "Other"
            confidence = 0.0

            for doc_type in self.document_types:
                if doc_type.lower() in cleaned_output.lower():
                    matched_purpose = doc_type
                    confidence = 1.0
                    break
            if matched_purpose == "Other":
                for doc_type in self.document_types:
                    if cleaned_output.lower() == doc_type.lower():
                        matched_purpose = doc_type
                        confidence = 1.0
                        break

            logger.info(f"Document classified as: {matched_purpose} (LLM raw output: '{llm_output}')")
            return {"purpose": matched_purpose, "confidence": confidence}
        else:
            logger.error("LLM classification failed or returned no output.")
            return {"purpose": "Unknown", "confidence": 0.0}

if __name__ == "__main__":
    invoice_content = """
    Invoice No: INV-2023-005
    Date: 2023-10-26
    Bill To: ABC Corp
    Amount Due: $1,234.50
    """

    email_content = """
    Subject: Support Request - Order ID #12345
    Dear Support Team,
    My name is John Doe and I am having an issue with my recent order.
    The product arrived damaged.
    Order ID: 12345
    """

    contract_content = """
    THIS AGREEMENT is made on this 1st day of January, 2024,
    BETWEEN: Party A, residing at...
    AND: Party B, located at...
    """

    unknown_content = """
    This is a random text that doesn't clearly fit any specific document type.
    It talks about general topics.
    """

    try:
        gemini_classifier = LLMClassifier()

        print("\n--- Gemini Classification Tests ---")
        print(f"Invoice: {gemini_classifier.classify_purpose(invoice_content)}")
        print(f"Email: {gemini_classifier.classify_purpose(email_content)}")
        print(f"Contract: {gemini_classifier.classify_purpose(contract_content)}")
        print(f"Unknown: {gemini_classifier.classify_purpose(unknown_content)}")

    except ValueError as e:
        print(f"\nSkipping Gemini test: {e}")
    except ImportError as e:
        print(f"\nSkipping Gemini test: {e}")
    except Exception as e:
        print(f"\nAn error occurred during Gemini test: {e}")