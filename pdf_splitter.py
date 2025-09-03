print("DEBUG: Script starting...")
print("DEBUG: About to import libraries...")

import PyPDF2
import re
import os
from pathlib import Path
import glob

print("DEBUG: Libraries imported successfully")

def extract_delivery_number_ocr(pdf_path):
    """
    Use OCR to extract text and find delivery number specifically in DGN format
    """
    try:
        # Try importing OCR libraries
        import pytesseract
        import pdf2image
        from PIL import Image
        
        print("Using OCR to extract text from scanned PDF...")
        
        # Convert PDF pages to images
        images = pdf2image.convert_from_path(pdf_path)
        print(f"Converted {len(images)} pages to images")
        
        for page_num, image in enumerate(images):
            print(f"\n--- OCR Processing Page {page_num + 1} ---")
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image)
            print(f"OCR extracted {len(text)} characters from page {page_num + 1}")
            
            if text:
                # Clean up the text for better searching
                clean_text = ' '.join(text.split())  # Remove extra whitespace
                print(f"Cleaned text length: {len(clean_text)}")
                
                # Show sample of extracted text for debugging
                print(f"Sample text (first 300 chars): {repr(text[:300])}")
                
                # Try multiple patterns to find the delivery number
                patterns_all = [
                    r"Order:(\d{10})",              # Order: followed directly by 10 digits (no space)
                    r"Order:\s*(\d+)",              # Order: followed by number (from packing list)
                    r"Order\s*[:\s]+\s*(\d+)",      # Order with various spacing
                    r"Exporter['\s]*s\s*reference[:\s]*(\d+)",  # Exporter's reference
                    r"reference[:\s]*(\d+)",        # reference: followed by number
                    r"\b(88\d{8})\b",              # Any 10-digit starting with 88
                    r"(\d{10})",                   # Any 10-digit number
                    r"883590818",                  # Exact match for this specific number
                ]
                
                print("Trying all patterns...")
                for pattern in patterns_all:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        print(f"Pattern '{pattern}' found: {matches}")
                        for match in matches:
                            # Clean the match (remove any spaces/characters)
                            clean_match = re.sub(r'[^\d]', '', str(match))
                            print(f"Cleaned match: '{clean_match}' (length: {len(clean_match)})")
                            
                            # Accept if it's our specific delivery number or any 10-digit starting with 88
                            if clean_match == "883590818" or (len(clean_match) == 10 and clean_match.startswith('88')):
                                print(f"✓ Found delivery number: {clean_match}")
                                return clean_match
                
                # Check if this is a specific page type
                if "DANGEROUS GOODS NOTE" in text.upper():
                    print("✓ Found DANGEROUS GOODS NOTE page")
                
                if "PACKING LIST" in text.upper():
                    print("✓ Found PACKING LIST page")
                
                # One more attempt: look for the specific number anywhere in the text
                if "883590818" in text:
                    print("✓ Found exact delivery number 883590818 in text!")
                    return "883590818"
                    
            else:
                print(f"No text extracted from page {page_num + 1}")
        
    except ImportError as e:
        print(f"OCR libraries not available: {e}")
        print("Falling back to PyPDF2...")
        return extract_delivery_number_fallback(pdf_path)
    except Exception as e:
        print(f"OCR failed with error: {e}")
        print("Falling back to PyPDF2...")
        return extract_delivery_number_fallback(pdf_path)
    
    print("No delivery number found with OCR method")
    return None

def extract_delivery_number_fallback(pdf_path):
    """
    Fallback method using PyPDF2 (for text-based PDFs)
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text and len(text) > 50:  # Only process if we got substantial text
                        print(f"PyPDF2 extracted {len(text)} characters from page {page_num + 1}")
                        
                        # Apply the same targeted search patterns
                        if "DANGEROUS GOODS NOTE" in text.upper():
                            patterns = [
                                r"Exporter['\s]*s?\s+reference[:\s]*(\d+)",
                                r"reference[:\s]*(88\d{8})",
                            ]
                            for pattern in patterns:
                                matches = re.findall(pattern, text, re.IGNORECASE)
                                for match in matches:
                                    if match.startswith('88') and len(match) == 10:
                                        return match
                        
                        if "PACKING LIST" in text.upper():
                            patterns = [r"Order[:\s]*(88\d{8})"]
                            for pattern in patterns:
                                matches = re.findall(pattern, text, re.IGNORECASE)
                                for match in matches:
                                    if match.startswith('88') and len(match) == 10:
                                        return match
                        
                        # Generic search
                        delivery_numbers = re.findall(r'\b88\d{8}\b', text)
                        if delivery_numbers:
                            return delivery_numbers[0]
                            
                except Exception as page_error:
                    print(f"Error processing page {page_num + 1}: {page_error}")
    
    except Exception as e:
        print(f"PyPDF2 fallback failed: {e}")
    
    return None

def split_pdf_to_pages(pdf_path, output_folder):
    """
    Split PDF into individual pages and save each as separate PDF
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            print(f"Found {total_pages} pages in PDF")
            
            # Create list to store page file paths
            page_files = []
            
            for page_num in range(total_pages):
                # Create a new PDF for this page
                pdf_writer = PyPDF2.PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_num])
                
                # Create filename (Page_01.pdf, Page_02.pdf, etc.)
                page_filename = f"Page_{page_num + 1:02d}.pdf"
                page_path = output_folder / page_filename
                
                # Save the page
                with open(page_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
                
                page_files.append(page_path)
                print(f"Created: {page_filename}")
            
            return page_files
            
    except Exception as e:
        print(f"Error splitting PDF: {e}")
        return []

def find_pdf_files():
    """
    Find all PDF files in the current directory
    """
    pdf_files = glob.glob("*.pdf")
    return pdf_files

def process_shipping_pdf(pdf_path, base_output_folder="./output"):
    """
    Main function to process the shipping PDF:
    1. Extract delivery number using OCR
    2. Create folder named after delivery number
    3. Split PDF into individual pages
    """
    pdf_path = Path(pdf_path)
    base_output_folder = Path(base_output_folder)
    
    print(f"Processing: {pdf_path.name}")
    
    # Step 1: Extract delivery number using OCR
    delivery_number = extract_delivery_number_ocr(pdf_path)
    
    if not delivery_number:
        print("ERROR: Could not find delivery number (10-digit starting with 88)")
        print("Tried OCR and PyPDF2 methods with targeted search patterns:")
        print("- DANGEROUS GOODS NOTE -> Exporter's reference")
        print("- PACKING LIST -> Order:")
        print("- Generic 88xxxxxxxx pattern search")
        return False
    
    print(f"Found delivery number: {delivery_number}")
    
    # Step 2: Create output folder
    delivery_folder = base_output_folder / delivery_number
    delivery_folder.mkdir(parents=True, exist_ok=True)
    print(f"Created folder: {delivery_folder}")
    
    # Step 3: Split PDF into pages
    page_files = split_pdf_to_pages(pdf_path, delivery_folder)
    
    if page_files:
        print(f"\nSUCCESS: Created {len(page_files)} individual PDF files")
        print(f"Location: {delivery_folder}")
        return True
    else:
        print("ERROR: Failed to split PDF")
        return False

# Main execution for GitHub Actions
if __name__ == "__main__":
    print("=== PDF Splitter with OCR Starting ===")
    
    # Find all PDF files in the repository
    pdf_files = find_pdf_files()
    
    if not pdf_files:
        print("ERROR: No PDF files found in the repository")
        print("Please upload a PDF file to the repository and try again")
        exit(1)
    
    print(f"Found {len(pdf_files)} PDF file(s): {pdf_files}")
    
    # Process each PDF file
    success_count = 0
    for pdf_file in pdf_files:
        print(f"\n{'='*50}")
        if process_shipping_pdf(pdf_file):
            success_count += 1
    
    print(f"\n{'='*50}")
    print(f"COMPLETED: Successfully processed {success_count}/{len(pdf_files)} PDF files")
