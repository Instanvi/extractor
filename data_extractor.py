import io
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import cv2
import numpy as np
import logging
from typing import List, Dict, Optional

class PDFExtractor:
    """
    1. PyMuPDF for direct text extraction
    2. pdfplumber for structured text with positioning
    3. OCR (Tesseract) as fallback for scanned documents
    """
    
    def __init__(self, ocr_lang: str = 'eng', dpi: int = 300):

        self.ocr_lang = ocr_lang
        self.dpi = dpi
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging for the extraction process."""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(binary)
        
        # Dilation to connect text components
        kernel = np.ones((1,1), np.uint8)
        dilated = cv2.dilate(denoised, kernel, iterations=1)
        
        return dilated
    
    def extract_with_pymupdf(self, contents: bytes) -> str:
        """Extract text using PyMuPDF."""
        try:
            doc = fitz.open(stream=contents, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            print(f'mupdf text; {text}')
            return text
        except Exception as e:
            self.logger.warning(f"PyMuPDF extraction failed: {str(e)}")
            return ""
            
    def extract_with_pdfplumber(self, contents: bytes) -> str:
        """Extract text using pdfplumber."""
        try:
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                print(f'plumber text; {text}')
                return text
        except Exception as e:
            self.logger.warning(f"pdfplumber extraction failed: {str(e)}")
            return ""
            
    def extract_with_ocr(self, contents: bytes) -> str:
        """Extract text using OCR."""
        try:
            images = convert_from_bytes(contents, dpi=self.dpi)
            text = ""
            
            for image in images:
                # Convert PIL Image to numpy array
                image_np = np.array(image)
                
                # Preprocess the image
                processed = self.preprocess_image(image_np)
                
                # Perform OCR with custom configuration
                custom_config = r'--oem 3 --psm 6'
                page_text = pytesseract.image_to_string(
                    processed, 
                    lang=self.ocr_lang,
                    config=custom_config
                )
                
                text += page_text + "\n"
            print(f'ocr text; {text}')
            return text
        except Exception as e:
            self.logger.warning(f"OCR extraction failed: {str(e)}")
            return ""
    
    def extract_text(self, contents: bytes) -> Dict[str, str]:
        """
        Extract text using all available methods and return results.
        """
        results = {
            #'pymupdf': self.extract_with_pymupdf(contents),
            'pdfplumber': self.extract_with_pdfplumber(contents),
            #'ocr': self.extract_with_ocr(contents)
        }
        
        # Combine results, prioritizing non-empty results
        combined_text = ""
        for method in ['pymupdf', 'pdfplumber', 'ocr']:
            if method in results and results[method].strip():
                combined_text = results[method]
                self.logger.info(f"Using text from {method}")
                break
        print(f'combined; {combined_text}')
        results['combined'] = combined_text
        return results

    def validate_extraction(self, text: str) -> bool:
        """
        Validate the extracted text quality.
        """
        if not text.strip():
            return False
            
        # Check if text contains common OCR artifacts
        suspicious_patterns = ['|ll|', '|||', '...', '   ', '###']
        suspicious_count = sum(1 for pattern in suspicious_patterns if pattern in text)
        
        # Calculate ratio of alphanumeric characters
        alphanumeric_ratio = sum(c.isalnum() for c in text) / len(text) if text else 0
        
        return suspicious_count < 3 and alphanumeric_ratio > 0.3

def extract_text_from_pdf(contents: bytes) -> str:
    """
    Main function to extract text from PDF with fallback mechanisms.
    """
    extractor = PDFExtractor()
    results = extractor.extract_text(contents)
    
    # Validate and return the best result
    if extractor.validate_extraction(results['combined']):
        return results['combined']
    else:
        # If combined result is not satisfactory, try other methods
        for method in ['pymupdf', 'pdfplumber', 'ocr']:
            if extractor.validate_extraction(results[method]):
                return results[method]
    
    # If all methods fail, return the combined result anyway
    return results['combined']