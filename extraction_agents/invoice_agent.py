import re
from utils import logger

class InvoiceExtractionAgent:
    def __init__(self):
        logger.info("Initialized Invoice Extraction Agent.")

    def extract_data(self, document_content):
        extracted_data = {
            "invoice_number": None,
            "date": None,
            "total_amount": None,
            "currency": None,
            "bill_to": None,
            "line_items": []
        }
        confidence_score = 0.0
        found_fields = 0
        total_expected_fields = 4

        if not document_content:
            logger.warning("Invoice document content is empty, cannot extract data.")
            return extracted_data, confidence_score

        normalized_content = document_content.strip()

        invoice_no_patterns = [
            r"Invoice No[\.:]?\s*([A-Za-z0-9\-\_]+)",
            r"Invoice #\s*([A-Za-z0-9\-\_]+)",
            r"INV\s*([A-Za-z0-9\-\_]+)",
            r"Ref(?:erence)? No[\.:]?\s*([A-Za-z0-9\-\_]+)"
        ]
        for pattern in invoice_no_patterns:
            match = re.search(pattern, normalized_content, re.IGNORECASE)
            if match:
                extracted_data["invoice_number"] = match.group(1).strip()
                logger.info(f"Extracted Invoice Number: {extracted_data['invoice_number']}")
                found_fields += 1
                break

        date_patterns = [
            r"Date[\.:]?\s*(\d{4}-\d{2}-\d{2})",
            r"Date[\.:]?\s*(\d{1,2}/\d{1,2}/\d{4})",
            r"Date[\.:]?\s*(\d{1,2}[/-](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[/-]\d{4})",
            r"(?:Invoice|Issue)?\s*Date\s*:\s*(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})"
        ]
        for pattern in date_patterns:
            match = re.search(pattern, normalized_content, re.IGNORECASE)
            if match:
                extracted_data["date"] = match.group(1).strip()
                logger.info(f"Extracted Date: {extracted_data['date']}")
                found_fields += 1
                break

        amount_patterns = [
            r"(?:Total|Amount Due|Balance Due)[\.:]?\s*([A-Z]{2,4}\s*[\d\.,]+|\$[\d\.,]+|€[\d\.,]+|£[\d\.,]+)",
            r"([\$\€\£]\s*[\d\.,]+(?:\s*[A-Z]{2,4})?)",
            r"Total[\.:]?\s*(\d[\d\.,]+\s*[A-Z]{2,4})"
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, normalized_content, re.IGNORECASE)
            if match:
                full_amount_str = match.group(1).strip()
                currency_match = re.search(r"([\$€£A-Z]{2,4})\s*([\d\.,]+)", full_amount_str, re.IGNORECASE)
                if currency_match:
                    extracted_data["currency"] = currency_match.group(1).strip().upper()
                    extracted_data["total_amount"] = currency_match.group(2).strip().replace(',', '')
                else:
                    if '$' in full_amount_str: extracted_data["currency"] = "USD"
                    elif '€' in full_amount_str: extracted_data["currency"] = "EUR"
                    elif '£' in full_amount_str: extracted_data["currency"] = "GBP"
                    extracted_data["total_amount"] = re.sub(r'[^\d\.]', '', full_amount_str.replace(',', ''))

                logger.info(f"Extracted Amount: {extracted_data['total_amount']} {extracted_data['currency']}")
                found_fields += 1
                break

        bill_to_match = re.search(r"(?:Bill To|Customer Name|Recipient)[\.:]?\s*([^\n\r]+)", normalized_content, re.IGNORECASE)
        if bill_to_match:
            bill_to_value = bill_to_match.group(1).strip()
            if ':' in bill_to_value and len(bill_to_value.split(':')) > 1:
                bill_to_value = bill_to_value.split(':')[0].strip()
            extracted_data["bill_to"] = bill_to_value
            logger.info(f"Extracted Bill To: {extracted_data['bill_to']}")
            found_fields += 1

        confidence_score = (found_fields / total_expected_fields) if total_expected_fields > 0 else 0.0
        logger.info(f"Invoice extraction completed with confidence: {confidence_score:.2f}")

        return extracted_data, confidence_score

if __name__ == "__main__":
    agent = InvoiceExtractionAgent()

    invoice_text_1 = """
    ABC Solutions
    123 Main St, Anytown, USA
    Invoice No: INV-2023-001
    Date: 2023-10-26
    Bill To: John Doe
              123 Customer Lane
              Custville, CA 90210
    Description         Qty Unit Price  Amount
    Product A            1    $100.00     $100.00
    Product B            2    $50.00      $100.00
    Subtotal:                             $200.00
    Tax (10%):                            $20.00
    Total Due:                            $220.00 USD
    """

    invoice_text_2 = """
    Reference No: 456789
    Order Date: 01/15/2024
    Recipient: Jane Smith Co.
    Amount Due: EUR 1,234.56
    (Details here...)
    """

    invoice_text_3 = """
    Invoice #998877
    Issued: 12-Dec-2023
    Amount Payable: £75.00
    Customer Name: Global Corp
    """

    invoice_text_4 = """
    A very plain document.
    No obvious invoice fields.
    """

    print("\n--- Invoice Extraction Test 1 ---")
    data, conf = agent.extract_data(invoice_text_1)
    print(f"Extracted Data: {data}")
    print(f"Confidence: {conf:.2f}")

    print("\n--- Invoice Extraction Test 2 ---")
    data, conf = agent.extract_data(invoice_text_2)
    print(f"Extracted Data: {data}")
    print(f"Confidence: {conf:.2f}")

    print("\n--- Invoice Extraction Test 3 ---")
    data, conf = agent.extract_data(invoice_text_3)
    print(f"Extracted Data: {data}")
    print(f"Confidence: {conf:.2f}")

    print("\n--- Invoice Extraction Test 4 (No Fields) ---")
    data, conf = agent.extract_data(invoice_text_4)
    print(f"Extracted Data: {data}")
    print(f"Confidence: {conf:.2f}")