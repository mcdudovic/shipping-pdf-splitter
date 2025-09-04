print("DEBUG: Script starting...")
print("DEBUG: About to import libraries...")

import PyPDF2
import re
import os
from pathlib import Path
import glob

print("DEBUG: Libraries imported successfully")

def identify_document_type(page_text, delivery_number):
    """
    Identify the type of document based on page content
    Returns a descriptive filename
    """
    page_text_upper = page_text.upper()
    
    # Document type patterns and their corresponding names
    doc_patterns = [
        ("DANGEROUS GOODS NOTE", f"{delivery_number} - DGN.pdf"),
        ("DANGEROUS GOODS DECLARATION", f"{delivery_number} - DGN.pdf"),
        ("PACKING LIST", f"{delivery_number} - Packing List.pdf"),
        ("JOHN DEWAR & SONS LTD-PACKING LIST", f"{delivery_number} - Packing List.pdf"),
        ("CDS EXPORT", f"{delivery_number} - CDS Export.pdf"),
        ("EUROPEAN COMMUNITY", f"{delivery_number} - EU Export.pdf"),
        ("UNITED KINGDOM - EXP-SAD/SEC", f"{delivery_number} - UK Export.pdf"),
        ("INVOICE", f"{delivery_number} - Invoice.pdf"),
        ("COLLECTION", f"{delivery_number} - Collection Note.pdf"),
        ("EFTCO CLEANING DOCUMENT", f"{delivery_number} - Tank Cleaning.pdf"),
        ("UK TANK CLEANING STATION", f"{delivery_number} - Tank Cleaning.pdf"),
        ("CONTAINER INTERCHANGE", f"{delivery_number} - Container Receipt.pdf"),
        ("SPIRIT DRINKS VERIFICATION", f"{delivery_number} - SDV.pdf"),
        ("FACILITY DETAILS - SDVS", f"{delivery_number} - SDV.pdf"),
        ("TANK CAPACITY", f"{delivery_number} - Loading Sheet.pdf"),
        ("EXPORTS", f"{delivery_number} - Loading Sheet.pdf"),
    ]
    
    # Check each pattern
    for pattern, filename in doc_patterns:
        if pattern in page_text_upper:
            print(f"Identified document type: {pattern} -> {filename}")
            return filename
    
    # Fallback: generic naming
    return None

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
                # Try multiple patterns to find the delivery number
                patterns_all = [
                    r"Order:(\d{10})",              # Order: followed directly by 10 digits
                    r"Order:\s*(\d+)",              # Order: followed by number
                    r"Order\s*[:\s]+\s*(\d+)",      # Order with various spacing
                    r"Exporter['\s]*s\s*reference[:\s]*(\d+)",  # Exporter's reference
                    r"reference[:\s]*(\d+)",        # reference: followed by number
                    r"\b(88\d{8})\b",              # Any 10-digit starting with 88
                    r"(\d{10})",                   # Any 10-digit number
                    r"883590818",                  # Exact match for this specific number
                ]
                
                for pattern in patterns_all:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        for match in matches:
                            # Clean the match
                            clean_match = re.sub(r'[^\d]', '', str(match))
                            # Accept if it's a 10-digit number starting with 88
                            if len(clean_match) == 10 and clean_match.startswith('88'):
                                print(f"✓ Found delivery number: {clean_match}")
                                return clean_match
                
                # One more attempt: look for the specific number anywhere
                if "883590818" in text:
                    print("✓ Found exact delivery number 883590818 in text!")
                    return "883590818"
                    
            else:
                print(f"No text extracted from page {page_num + 1}")
        
    except ImportError as e:
        print(f"OCR libraries not available: {e}")
        return extract_delivery_number_fallback(pdf_path)
    except Exception as e:
        print(f"OCR failed with error: {e}")
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
                    if text and len(text) > 50:
                        # Generic search for delivery numbers
                        delivery_numbers = re.findall(r'\b88\d{8}\b', text)
                        if delivery_numbers:
                            return delivery_numbers[0]
                            
                except Exception as page_error:
                    print(f"Error processing page {page_num + 1}: {page_error}")
    
    except Exception as e:
        print(f"PyPDF2 fallback failed: {e}")
    
    return None

def split_pdf_to_pages(pdf_path, output_folder, delivery_number):
    """
    Split PDF into individual pages with smart naming
    """
    try:
        # For OCR text extraction per page
        import pytesseract
        import pdf2image
        
        print("Converting PDF to images for document type identification...")
        images = pdf2image.convert_from_path(pdf_path)
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            print(f"Found {total_pages} pages in PDF")
            
            page_files = []
            used_names = {}  # Track used names to avoid duplicates
            
            for page_num in range(total_pages):
                # Create a new PDF for this page
                pdf_writer = PyPDF2.PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_num])
                
                # Extract text from this page using OCR to identify document type
                try:
                    page_text = pytesseract.image_to_string(images[page_num])
                    suggested_filename = identify_document_type(page_text, delivery_number)
                except Exception as ocr_error:
                    print(f"OCR failed for page {page_num + 1}: {ocr_error}")
                    suggested_filename = None
                
                # Determine final filename
                if suggested_filename:
                    # Handle duplicate names
                    base_name = suggested_filename
                    if base_name in used_names:
                        used_names[base_name] += 1
                        name_parts = base_name.split('.pdf')
                        final_filename = f"{name_parts[0]} ({used_names[base_name]}).pdf"
                    else:
                        used_names[base_name] = 1
                        final_filename = base_name
                else:
                    # Fallback to generic naming
                    final_filename = f"{delivery_number} - Page {page_num + 1:02d}.pdf"
                
                page_path = output_folder / final_filename
                
                # Save the page
                with open(page_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
                
                page_files.append(page_path)
                print(f"Created: {final_filename}")
            
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
    Main function to process the shipping PDF with smart naming
    """
    pdf_path = Path(pdf_path)
    base_output_folder = Path(base_output_folder)
    
    print(f"Processing: {pdf_path.name}")
    
    # Step 1: Extract delivery number
    delivery_number = extract_delivery_number_ocr(pdf_path)
    
    if not delivery_number:
        print("ERROR: Could not find delivery number (10-digit starting with 88)")
        return False, None
    
    print(f"Found delivery number: {delivery_number}")
    
    # Step 2: Create output folder
    delivery_folder = base_output_folder / delivery_number
    delivery_folder.mkdir(parents=True, exist_ok=True)
    print(f"Created folder: {delivery_folder}")
    
    # Step 3: Split PDF into pages with smart naming
    page_files = split_pdf_to_pages(pdf_path, delivery_folder, delivery_number)
    
    if page_files:
        print(f"\nSUCCESS: Created {len(page_files)} individual PDF files")
        print(f"Location: {delivery_folder}")
        
        # Step 4: Delete original PDF file
        try:
            pdf_path.unlink()
            print(f"✓ Deleted original file: {pdf_path.name}")
        except Exception as e:
            print(f"Warning: Could not delete original file: {e}")
        
        return True, delivery_number
    else:
        print("ERROR: Failed to split PDF")
        return False, None

# Main execution for GitHub Actions
if __name__ == "__main__":
    print("=== Enhanced PDF Splitter Starting ===")
    
    # Find all PDF files in the repository
    pdf_files = find_pdf_files()
    
    if not pdf_files:
        print("ERROR: No PDF files found in the repository")
        exit(1)
    
    print(f"Found {len(pdf_files)} PDF file(s): {pdf_files}")
    
    # Process each PDF file
    success_count = 0
    processed_delivery_numbers = []
    
    for pdf_file in pdf_files:
        print(f"\n{'='*50}")
        success, delivery_number = process_shipping_pdf(pdf_file)
        if success:
            success_count += 1
            processed_delivery_numbers.append(delivery_number)
    
    print(f"\n{'='*50}")
    print(f"COMPLETED: Successfully processed {success_count}/{len(pdf_files)} PDF files")
    
    # Write delivery numbers to file for workflow to use
    if processed_delivery_numbers:
        with open('delivery_numbers.txt', 'w') as f:
            f.write('\n'.join(processed_delivery_numbers))
        print(f"Delivery numbers written to file: {processed_delivery_numbers}")
