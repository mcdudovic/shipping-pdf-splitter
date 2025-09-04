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
    Use OCR to extract text and find delivery number with enhanced debugging
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
                # Enhanced debugging - show more text
                print(f"Sample text (first 500 chars): {repr(text[:500])}")
                print(f"Full text length: {len(text)}")

                # Debug: Look specifically for 88 numbers in the text
                if "88" in text:
                    print("Found '88' somewhere in text")
                    # Find all instances of 88 followed by digits
                    debug_matches = re.findall(r'88\d+', text)
                    print(f"All '88' + digits found: {debug_matches}")
                    
                    # Check for the specific number we expect
                    if "883612546" in text:
                        print("✓ Found exact number 883612546 in text!")
                    else:
                        print("✗ 883612546 not found in text")
                else:
                    print("No '88' found anywhere in text")
                
                # PRIORITY PATTERNS: 88-prefixed numbers checked FIRST
                patterns_all = [
                    # PRIORITY: 88-prefixed numbers anywhere in document - CHECK FIRST!
                    r"\b(88\d{8})\b",                   # 883612546 anywhere in text
                    r"88(\d{8})",                       # 88 followed by 8 digits (more flexible)
                    r"(88\d{8})",                       # 88 + 8 digits without word boundaries
                    
                    # Then check specific fields
                    r"Customer\s+Ref[:\s]*(\d{10})",     # Customer Ref: 883612546
                    r"Customer\s*Ref[:\s]*(\d{10})",     # Customer Ref:883612546 
                    r"Customer\s+Reference[:\s]*(\d{10})", # Customer Reference: 
                    r"Order[:\s]*(\d{10})",              # Order: (backup)
                    r"Order[:\s]*(\d+)",                 # Order: followed by any digits
                    
                    # Dangerous Goods Note patterns  
                    r"Exporter['\s]*s?\s*reference[:\s]*(\d{10})", # Exporter's reference
                    r"Exporters?\s*reference[:\s]*(\d{10})",       # Exporters reference
                    r"reference[:\s]*(\d{10})",          # reference: 883612546
                    
                    # Generic field patterns - look for common shipping fields
                    r"Ref[:\s]*(\d{10})",               # Ref: 883612546
                    r"Reference[:\s]*(\d{10})",         # Reference: 883612546  
                    r"Number[:\s]*(\d{10})",            # Number: 883612546
                    r"ID[:\s]*(\d{10})",                # ID: 883612546
                    r"Booking[:\s]*(\d{10})",           # Booking: 883612546
                    
                    # Backup - any 10-digit number (lowest priority)
                    r"\b(\d{10})\b",                    # Any 10-digit number
                ]
                
                print("Trying delivery number patterns (88-prefix priority)...")
                
                for i, pattern in enumerate(patterns_all):
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        print(f"Pattern {i+1} '{pattern}' found: {matches}")
                        for match in matches:
                            # Clean the match
                            clean_match = re.sub(r'[^\d]', '', str(match))
                            print(f"Cleaned match: '{clean_match}' (length: {len(clean_match)})")
                            
                            # Accept 10-digit numbers or 8-digit numbers with 88 prefix
                            if (len(clean_match) == 10 and clean_match.startswith('88')) or \
                               (len(clean_match) == 8 and i < 3):  # First 3 patterns are 88-specific
                                if len(clean_match) == 8:
                                    clean_match = "88" + clean_match  # Add the 88 prefix back
                                print(f"✓ Found delivery number: {clean_match}")
                                return clean_match
                            elif len(clean_match) == 10 and i >= 3:  # Other 10-digit patterns
                                print(f"Found non-88 number: {clean_match}, continuing to look for 88-prefix...")
                                continue
                
                # If we get here, no 88-prefixed number was found, look for any 10-digit as fallback
                print("No 88-prefixed number found, checking for any 10-digit numbers...")
                fallback_matches = re.findall(r'\b(\d{10})\b', text)
                if fallback_matches:
                    clean_match = fallback_matches[0]
                    print(f"✓ Using fallback delivery number: {clean_match}")
                    return clean_match
                
                # Check if this is a specific page type for debugging
                if "DANGEROUS GOODS NOTE" in text.upper():
                    print("✓ Found DANGEROUS GOODS NOTE page")
                
                if "PACKING LIST" in text.upper():
                    print("✓ Found PACKING LIST page")
                    
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
                        print(f"PyPDF2 extracted {len(text)} characters from page {page_num + 1}")
                        
                        # Use same priority patterns as OCR method
                        patterns = [
                            r"\b(88\d{8})\b",               # 88-prefix first
                            r"Customer\s+Ref[:\s]*(\d{10})",
                            r"Order[:\s]*(\d{10})",
                            r"reference[:\s]*(\d{10})",
                            r"\b(\d{10})\b",                # Any 10-digit last
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, text, re.IGNORECASE)
                            for match in matches:
                                clean_match = re.sub(r'[^\d]', '', str(match))
                                if len(clean_match) == 10:
                                    return clean_match
                            
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
        print("ERROR: Could not find delivery number")
        print("Tried patterns in priority order:")
        print("1. Any 10-digit number starting with 88 (priority)")
        print("2. Customer Ref: [number]")
        print("3. Order: [number]") 
        print("4. Exporter's reference: [number]")
        print("5. Any 10-digit number (fallback)")
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
