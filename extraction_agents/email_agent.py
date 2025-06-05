import json
from utils import logger
from config import (
    GEMINI_API_KEY, GEMINI_MODEL_NAME
)

try:
    import google.generativeai as genai
    logger.info("Google Generative AI client imported for Email Agent.")
except ImportError:
    genai = None
    logger.warning("Google Generative AI library not found. Please run 'pip install google-generativeai'")


class EmailExtractionAgent:
    def __init__(self):
        self.llm_provider = "gemini"
        self.client = None
        self.model_name = None

        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in .env or environment variables for Email Agent.")
        if genai:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model_name = GEMINI_MODEL_NAME
            self.client = genai.GenerativeModel(self.model_name)
            logger.info(f"Initialized Gemini Email Extraction Agent with model: {self.model_name}")
        else:
            raise ImportError("Google Generative AI library is not installed. Please run 'pip install google-generativeai'")

    def _get_gemini_response(self, prompt):
        try:
            response = self.client.generate_content(prompt, generation_config=genai.types.GenerationConfig(
                response_mime_type='application/json'
            ))
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error calling Gemini API for email extraction: {e}")
            return None

    def extract_data(self, document_content):
        extracted_data = {
            "customer_name": None,
            "issue_description": None,
            "order_id": None,
            "email_subject": None,
            "sender_email": None
        }
        confidence_score = 0.0

        if not document_content:
            logger.warning("Email content is empty, cannot extract data.")
            return extracted_data, confidence_score

        prompt = f"""
        Analyze the following email content and extract the following information:
        - Customer Name (the name of the person sending or whose issue it is)
        - Issue Description (a concise summary of the problem or request)
        - Order ID (any identifier that looks like an order number, e.g., numbers, alphanumeric codes)
        - Email Subject (if present, the subject of the email)
        - Sender Email (if present, the email address of the sender)

        If a piece of information is not found, use 'N/A' for that field.
        Return the extracted information as a JSON object with keys:
        "customer_name", "issue_description", "order_id", "email_subject", "sender_email".

        Email Content:
        ---
        {document_content[:4000]}
        ---
        """
        logger.info(f"Sending email extraction prompt to {self.llm_provider}...")

        llm_output = None
        llm_output = self._get_gemini_response(prompt)


        if llm_output:
            try:
                extracted_data = json.loads(llm_output)
                for key in ["customer_name", "issue_description", "order_id", "email_subject", "sender_email"]:
                    if key not in extracted_data:
                        extracted_data[key] = "N/A"
                confidence_score = 1.0
                logger.info(f"Successfully extracted email data: {extracted_data}")
            except json.JSONDecodeError as e:
                logger.error(f"LLM returned invalid JSON for email extraction: {e}\nRaw output: {llm_output}")
                confidence_score = 0.5
            except Exception as e:
                logger.error(f"Error processing LLM output for email extraction: {e}\nRaw output: {llm_output}")
                confidence_score = 0.5
        else:
            logger.error("LLM email extraction failed or returned no output.")
            confidence_score = 0.0

        return extracted_data, confidence_score

if __name__ == "__main__":
    email_content_1 = """
    From: john.doe@example.com
    To: support@company.com
    Subject: Issue with my recent purchase - Order #XYZ-789
    Date: Tue, 4 Jun 2024 10:00:00 +0000

    Dear Support,
    My name is John Doe and I am writing to report a problem with my order ID XYZ-789.
    The item I received was incorrect; I ordered a blue widget but received a red one.
    Please advise on how to proceed with an exchange.
    Thank you,
    John
    """

    email_content_2 = """
    From: sales@vendor.com
    Subject: Your Latest Order Confirmation
    Date: Mon, 3 Jun 2024 14:30:00 -0500

    Hi Customer,
    Your order has been confirmed. No specific issue reported here.
    """

    email_content_3 = """
    This is just a random text. No email format, no clear fields.
    """

    try:
        gemini_email_agent = EmailExtractionAgent()
        print("\n--- Gemini Email Extraction Test 1 ---")
        data, conf = gemini_email_agent.extract_data(email_content_1)
        print(f"Extracted Data: {data}")
        print(f"Confidence: {conf:.2f}")

        print("\n--- Gemini Email Extraction Test 2 ---")
        data, conf = gemini_email_agent.extract_data(email_content_2)
        print(f"Extracted Data: {data}")
        print(f"Confidence: {conf:.2f}")

        print("\n--- Gemini Email Extraction Test 3 ---")
        data, conf = gemini_email_agent.extract_data(email_content_3)
        print(f"Extracted Data: {data}")
        print(f"Confidence: {conf:.2f}")

    except ValueError as e:
        print(f"\nSkipping Gemini Email Agent test: {e}")
    except ImportError as e:
        print(f"\nSkipping Gemini Email Agent test: {e}")
    except Exception as e:
        print(f"\nAn error occurred during Gemini Email Agent test: {e}")