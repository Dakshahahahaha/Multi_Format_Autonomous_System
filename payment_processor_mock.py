from utils import logger, get_current_timestamp

class PaymentProcessorMock:
    def __init__(self):
        logger.info("Initialized Mock Payment Processor.")

    def process_invoice_payment(self, invoice_number, amount, currency="USD"):
        if invoice_number and amount:
            logger.info(f"MOCK PAYMENT: Initiating payment for Invoice No. '{invoice_number}' for {amount} {currency} at {get_current_timestamp()}.")
            return {
                "status": "success",
                "message": f"Invoice {invoice_number} of {amount} {currency} processed successfully via mock payment service.",
                "transaction_time": get_current_timestamp()
            }
        else:
            logger.warning(f"MOCK PAYMENT: Could not process payment. Missing invoice number or amount.")
            return {
                "status": "failed",
                "message": "Missing invoice number or amount for payment processing.",
                "transaction_time": get_current_timestamp()
            }

if __name__ == "__main__":
    processor = PaymentProcessorMock()
    result = processor.process_invoice_payment("INV-2024-007", "500.00", "USD")
    print(result)
    result_fail = processor.process_invoice_payment(None, "100.00")
    print(result_fail)