import fitz
import pytesseract
from PIL import Image
import io
import os
from utils import logger
from config import TESSERACT_CMD

class OCRProcessor:
    def __init__(self):
        try:
            pytesseract.get_tesseract_version()
            logger.info(f"Tesseract found: {pytesseract.get_tesseract_version()}")
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract OCR engine not found. Please install it or set TESSERACT_CMD in .env.")
            raise FileNotFoundError("Tesseract OCR engine is not installed or not in PATH.")

    def _extract_text_from_pdf(self, pdf_path):
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text += page.get_text()
            doc.close()
            logger.info(f"Extracted text directly from {pdf_path} (text-searchable).")
            return text
        except Exception as e:
            logger.warning(f"Error extracting text directly from {pdf_path}: {e}")
            return ""

    def _ocr_pdf_page(self, page):
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            text = pytesseract.image_to_string(img)
            logger.debug(f"Performed OCR on a page. Text length: {len(text)}")
            return text
        except Exception as e:
            logger.error(f"Error during OCR on a PDF page: {e}")
            return ""

    def process_pdf(self, pdf_path):
        if not os.path.exists(pdf_path):
            return None, f"PDF file not found: {pdf_path}"

        logger.info(f"Processing PDF: {pdf_path}")
        text_from_pdf = self._extract_text_from_pdf(pdf_path)

        if len(text_from_pdf.strip()) < 50:
            logger.info(f"Direct text extraction yielded little content. Attempting OCR for {pdf_path}...")
            ocr_text = ""
            try:
                doc = fitz.open(pdf_path)
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    ocr_text += self._ocr_pdf_page(page) + "\n"
                doc.close()
                logger.info(f"OCR completed for {pdf_path}. Total OCR text length: {len(ocr_text)}")
                return ocr_text, None
            except Exception as e:
                logger.error(f"Failed to process PDF {pdf_path} with OCR: {e}")
                return None, f"Failed to OCR PDF: {e}"
        else:
            logger.info(f"Used direct text extraction for {pdf_path}.")
            return text_from_pdf, None

if __name__ == "__main__":
    ocr_processor = OCRProcessor()

    dummy_pdf_path = "dummy_test_ocr.pdf"
    try:
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Hello World from PDF!\nThis is a test document.", fontsize=12)
        doc.save(dummy_pdf_path)
        doc.close()

        print(f"Created dummy PDF at {dummy_pdf_path}")

        extracted_text, error = ocr_processor.process_pdf(dummy_pdf_path)
        if extracted_text:
            print("\n--- OCR Processor Test ---")
            print(f"Extracted Text:\n{extracted_text[:500]}...")
        if error:
            print(f"Error: {error}")

    except Exception as e:
        print(f"Could not create dummy PDF or run OCR test: {e}. Make sure PyMuPDF, Pillow, and Tesseract are installed.")
        print("To fully test, you might need a real PDF file, e.g., an image-based invoice.")
    finally:
        if os.path.exists(dummy_pdf_path):
            os.remove(dummy_pdf_path)
            print(f"Removed dummy PDF: {dummy_pdf_path}")