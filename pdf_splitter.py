print("DEBUG: Script starting...")
print("DEBUG: About to import libraries...")

import PyPDF2
import re
import os
from pathlib import Path
import glob

print("DEBUG: Libraries imported successfully")

def is_valid_delivery_number(number_str):
    """
    Strict validation: only accept 9-digit numbers starting with 88, 
    or 10-digit numbers starting with 088
    """
    if not number_str or not number_str.isdigit():
        return False
    
    if len(number_str) == 9 and number_str.startswith('88'):
        return True
    elif len(number_str) == 10 and number_str.startswith('088'):
        return True
    else:
        return False

def extract_delivery_number_from_packing_list(text):
    """
    Priority 1: Extract from Packing List - Order: or Customer Ref:
    """
    if "PACKING LIST" not in text.upper():
        return None
    
    print("Searching in PACKING LIST...")
    
    patterns = [
        r"Customer\s+Ref[:\s]*(\d{9,10})",     # Customer Ref: 883612546
        r"Customer\s*Ref[:\s]*(\d{9,10})",     # Customer Ref:883612546
        r"Order[:\s]*(\d{9,10})",              # Order: 4530323857
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean_match = re.sub(r'[^\d]', '', match)
            print(f"Found in packing list: {clean_match}")
            if is_valid_delivery_number(clean_match):
                # Convert 088xxxxxxx to 88xxxxxxx format
                if len(clean_match) == 10 and clean_match.startswith('088'):
                    clean_match = clean_match[1:]  # Remove leading 0
                print(f"✓ Valid delivery number from PACKING LIST: {clean_match}")
                return clean_match
    
    return None

def extract_delivery_number_from_dgn(text):
    """
    Priority 2: Extract from DGN - Exporter's reference box 4
    """
    if "DANGEROUS GOODS" not in text.upper():
        return None
    
    print("Searching in DANGEROUS GOODS NOTE...")
    
    patterns = [
        r"Exporter['\s]*s\s*reference[:\s]*(\d{9,10})",  # Exporter's reference
        r"Exporters?\s*reference[:\s]*(\d{9,10})",       # Exporters reference
        r"reference[:\s]*(\d{9,10})",                    # reference: 883612546
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean_match = re.sub(r'[^\d]', '', match)
            print(f"Found in DGN: {clean_match}")
            if is_valid_delivery_number(clean_match):
                if len(clean_match) == 10 and clean_match.startswith('088'):
                    clean_match = clean_match[1:]
                print(f"✓ Valid delivery number from DGN: {clean_match}")
                return clean_match
    
    return None

def extract_delivery_number_from_cds(text):
    """
    Priority 3: Extract from CDS Export - box 40 or LRN box
    """
    if "CDS" not in text.upper() and "EXPORT" not in text.upper():
        return None
    
    print("Searching in CDS EXPORT...")
    
    patterns = [
        r"LRN[:\s]*(\d{9,10})",                # LRN box
        r"0(\d{8})",                            # Numbers with leading 0 (9 digits total)
        r"\b(088\d{7})\b",                      # 088xxxxxxx (10 digits)
        r"\b(88\d{7})\b",                       # 88xxxxxxx (9 digits)
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean_match = re.sub(r'[^\d]', '', match)
            print(f"Found in CDS: {clean_match}")
            if is_valid_delivery_number(clean_match):
                if len(clean_match) == 10 and clean_match.startswith('088'):
                    clean_match = clean_match[1:]
                print(f"✓ Valid delivery number from CDS: {clean_match}")
                return clean_match
    
    return None

def extract_delivery_number_from_ead(text):
    """
    Priority 4: Extract from Export Accompanying Document (EAD)
    """
    if "EXPORT" not in text.upper() and "ACCOMPANYING" not in text.upper():
        # Also check for EUROPEAN COMMUNITY
        if "EUROPEAN COMMUNITY" not in text.upper():
            return None
    
    print("Searching in EAD/EXPORT DOCUMENT...")
    
    patterns = [
        r"Reference\s+number[:\s]*[^\d]*(\d{9,10})",     # Reference numbers box
        r"0(\d{8})",                                      # Numbers with leading 0
        r"\b(088\d{7})\b",                               # 088xxxxxxx
        r"\b(88\d{7})\b",                                # 88xxxxxxx
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean_match = re.sub(r'[^\d]', '', match)
            print(f"Found in EAD: {clean_match}")
            if is_valid_delivery_number(clean_match):
                if len(clean_match) == 10 and clean_match.startswith('088'):
                    clean_match = clean_match[1:]
                print(f"✓ Valid delivery number from EAD: {clean_match}")
                return clean_match
    
    return None

def extract_delivery_number_from_sad(text):
    """
    Priority 5: Extract from SAD sheet
    """
    if "UNITED KINGDOM" not in text.upper() and "EXP-SAD" not in text.upper():
        return None
    
    print("Searching in SAD SHEET...")
    
    patterns = [
        r"Reference\s+number[:\s]*[^\d]*(\d{9,10})",     # Reference numbers box
        r"0(\d{8})",                                      # Numbers with leading 0  
        r"\b(088\d{7})\b",                               # 088xxxxxxx
        r"\b(88\d{7})\b",                                # 88xxxxxxx
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean_match = re.sub(r'[^\d]', '', match)
            print(f"Found in SAD: {clean_match}")
            if is_valid_delivery_number(clean_match):
                if len(clean_match) == 10 and clean_match.startswith('088'):
                    clean_match = clean_match[1:]
                print(f"✓ Valid delivery number from SAD: {clean_match}")
                return clean_match
    
    return None

def extract_delivery_number_from_certificate(text):
    """
    Priority 6: Extract from ISOCON/Certificate of Cleanliness
    """
    if "CERTIFICATE" not in text.upper() and "CLEANLINESS" not in text.upper() and "ISOCON" not in text.upper():
        return None
    
    print("Searching in CERTIFICATE OF CLEANLINESS...")
    
    patterns = [
        r"CUSTOMER\s+LOAD(?:ING)?\s+REF[:\s]*(\d{9,10})", # CUSTOMER LOAD REF: or CUSTOMER LOADING REF:
        r"LOAD\s+REF[:\s]*(\d{9,10})",                    # LOAD REF:
        r"\b(88\d{7})\b",                                  # 88xxxxxxx anywhere
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            clean_match = re.sub(r'[^\d]', '', match)
            print(f"Found in Certificate: {clean_match}")
            if is_valid_delivery_number(clean_match):
                if len(clean_match) == 10 and clean_match.startswith('088'):
                    clean_match = clean_match[1:]
                print(f"✓ Valid delivery number from Certificate: {clean_match}")
                return clean_match
    
    return None

def extract_delivery_number_hierarchical(text):
    """
    Search for delivery number using hierarchical approach
    """
    print(f"\n=== HIERARCHICAL DELIVERY NUMBER SEARCH ===")
    print(f"Text sample (first 300 chars): {repr(text[:300])}")
    
    # Priority 1: Packing List
    result = extract_delivery_number_from_packing_list(text)
    if result:
        return result
    
    # Priority 2: DGN
    result = extract_delivery_number_from_dgn(text)
    if result:
        return result
    
    # Priority 3: CDS Export
    result = extract_delivery_number_from_cds(text)
    if result:
        return result
    
    # Priority 4: EAD
    result = extract_delivery_number_from_ead(text)
    if result:
        return result
    
    # Priority 5: SAD
    result = extract_delivery_number_from_sad(text)
    if result:
        return result
    
    # Priority 6: Certificate
    result = extract_delivery_number_from_certificate(text)
    if result:
        return result
    
    print("No valid delivery number found in this page")
    return None

def identify_document_type(page_text, delivery_number):
    """
    Identify the type of document based on page content
    """
    page_text_upper = page_text.upper()
    
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
        ("CERTIFICATE OF CLEANLINESS", f"{delivery_number} - Certificate of Cleanliness.pdf"),
        ("ISOCON", f"{delivery_number} - Certificate of Cleanliness.pdf"),
        ("CONTAINER INTERCHANGE", f"{delivery_number} - Container Receipt.pdf"),
        ("SPIRIT DRINKS VERIFICATION", f"{delivery_number} - SDV.pdf"),
        ("FACILITY DETAILS - SDVS", f"{delivery_number} - SDV.pdf"),
        ("TANK CAPACITY", f"{delivery_number} - Loading Sheet.pdf"),
        ("EXPORTS", f"{delivery_number} - Loading Sheet.pdf"),
    ]
    
    for pattern, filename in doc_patterns:
        if pattern in page_text_upper:
            print(f"Identified document type: {pattern} -> {filename}")
            return filename
    
    return None

def extract_delivery_number_ocr(pdf_path):
    """
    Use OCR to extract delivery number using hierarchical search
    """
    try:
        import pytesseract
        import pdf2image
        from PIL import Image
        
        print("Using OCR with hierarchical search...")
        
        images = pdf2image.convert_from_path(pdf_path)
        print(f"Converted {len(images)} pages to images")
        
        for page_num, image in enumerate(images):
            print(f"\n--- OCR Processing Page {page_num + 1} ---")
            
            text = pytesseract.image_to_string(image)
            print(f"OCR extracted {len(text)} characters from page {page_num + 1}")
            
            if text and len(text) > 100:  # Only process substantial text
                # Use hierarchical search
                delivery_number = extract_delivery_number_hierarchical(text)
                if delivery_number:
                    return delivery_number
            else:
                print(f"Insufficient text extracted from page {page_num + 1}")
        
    except ImportError as e:
        print(f"OCR libraries not available: {e}")
        return extract_delivery_number_fallback(pdf_path)
    except Exception as e:
        print(f"OCR failed with error: {e}")
        return extract_delivery_number_fallback(pdf_path)
    
    print("No valid delivery number found with OCR method")
    return None

def extract_delivery_number_fallback(pdf_path):
    """
    Fallback method using PyPDF2 with hierarchical search
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text and len(text) > 100:
                        print(f"PyPDF2 extracted {len(text)} characters from page {page_num + 1}")
                        delivery_number = extract_delivery_number_hierarchical(text)
                        if delivery_number:
                            return delivery_number
                            
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
        import pytesseract
        import pdf2image
        
        print("Converting PDF to images for document type identification...")
        images = pdf2image.convert_from_path(pdf_path)
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            print(f"Found {total_pages} pages in PDF")
            
            page_files = []
            used_names = {}
            
            for page_num in range(total_pages):
                pdf_writer = PyPDF2.PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_num])
                
                try:
                    page_text = pytesseract.image_to_string(images[page_num])
                    suggested_filename = identify_document_type(page_text, delivery_number)
                except Exception as ocr_error:
                    print(f"OCR failed for page {page_num + 1}: {ocr_error}")
                    suggested_filename = None
                
                if suggested_filename:
                    base_name = suggested_filename
                    if base_name in used_names:
                        used_names[base_name] += 1
                        name_parts = base_name.split('.pdf')
                        final_filename = f"{name_parts[0]} ({used_names[base_name]}).pdf"
                    else:
                        used_names[base_name] = 1
                        final_filename = base_name
                else:
                    final_filename = f"{delivery_number} - Page {page_num + 1:02d}.pdf"
                
                page_path = output_folder / final_filename
                
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
    Main function to process shipping PDF with strict validation
    """
    pdf_path = Path(pdf_path)
    base_output_folder = Path(base_output_folder)
    
    print(f"Processing: {pdf_path.name}")
    
    # Extract delivery number using hierarchical search
    delivery_number = extract_delivery_number_ocr(pdf_path)
    
    if not delivery_number:
        print("ERROR: Could not find valid delivery number")
        print("STRICT VALIDATION FAILED:")
        print("- Must be exactly 9 digits starting with '88'")
        print("- Or exactly 10 digits starting with '088'")
        print("- Searched in priority order:")
        print("  1. Packing List (Order/Customer Ref)")
        print("  2. DGN (Exporter's reference)")
        print("  3. CDS Export (box 40/LRN)")
        print("  4. EAD (Reference Numbers)")
        print("  5. SAD (Reference Numbers/box 40)")
        print("  6. Certificate (Customer Load Ref)")
        return False, None
    
    print(f"✓ VALIDATED delivery number: {delivery_number}")
    
    # Create output folder
    delivery_folder = base_output_folder / delivery_number
    delivery_folder.mkdir(parents=True, exist_ok=True)
    print(f"Created folder: {delivery_folder}")
    
    # Split PDF into pages
    page_files = split_pdf_to_pages(pdf_path, delivery_folder, delivery_number)
    
    if page_files:
        print(f"\nSUCCESS: Created {len(page_files)} individual PDF files")
        print(f"Location: {delivery_folder}")
        
        # Delete original PDF
        try:
            pdf_path.unlink()
            print(f"✓ Deleted original file: {pdf_path.name}")
        except Exception as e:
            print(f"Warning: Could not delete original file: {e}")
        
        return True, delivery_number
    else:
        print("ERROR: Failed to split PDF")
        return False, None

# Main execution
if __name__ == "__main__":
    print("=== HIERARCHICAL PDF SPLITTER STARTING ===")
    
    pdf_files = find_pdf_files()
    
    if not pdf_files:
        print("ERROR: No PDF files found in the repository")
        exit(1)
    
    print(f"Found {len(pdf_files)} PDF file(s): {pdf_files}")
    
    success_count = 0
    processed_delivery_numbers = []
    
    for pdf_file in pdf_files:
        print(f"\n{'='*60}")
        success, delivery_number = process_shipping_pdf(pdf_file)
        if success:
            success_count += 1
            processed_delivery_numbers.append(delivery_number)
    
    print(f"\n{'='*60}")
    print(f"COMPLETED: Successfully processed {success_count}/{len(pdf_files)} PDF files")
    
    if processed_delivery_numbers:
        with open('delivery_numbers.txt', 'w') as f:
            f.write('\n'.join(processed_delivery_numbers))
        print(f"Delivery numbers written to file: {processed_delivery_numbers}")
