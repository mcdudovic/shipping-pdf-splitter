print("DEBUG: Script starting...")
print("DEBUG: About to import libraries...")

import PyPDF2
import re
import os
from pathlib import Path
import glob
import zipfile
import shutil
from datetime import datetime

print("DEBUG: Libraries imported successfully")

# SharePoint network path
SHAREPOINT_PATH = Path(r"C:\Users\sttaylor\Bacardi-Martini, Inc\GlasgowFS - Split PDFs")

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

def extract_filling_date(text):
    """
    Extract filling date from packing list
    """
    if "PACKING LIST" not in text.upper() and "FILLING DATE" not in text.upper():
        return None
    
    print("Searching for FILLING DATE...")
    
    # Look for FILLING DATE followed by a date
    patterns = [
        r"FILLING\s+DATE[:\s]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})",    # DD/MM/YYYY or DD-MM-YYYY
        r"FILLING\s+DATE[:\s]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2})",     # DD/MM/YY or DD-MM-YY
        r"FILLING[:\s]+DATE[:\s]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})",  # FILLING: DATE
        r"FILLING[:\s]+DATE[:\s]*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2})",   # FILLING: DATE YY
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            date_str = matches[0]
            print(f"Found filling date: {date_str}")
            
            # Convert to DD.MM.YY format
            try:
                # Handle different separators and year formats
                date_clean = re.sub(r'[/.-]', '/', date_str)
                parts = date_clean.split('/')
                
                if len(parts) == 3:
                    day, month, year = parts
                    
                    # Convert year to YY format
                    if len(year) == 4:
                        year = year[-2:]  # Take last 2 digits
                    
                    # Format as DD.MM.YY
                    formatted_date = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
                    print(f"Formatted filling date: {formatted_date}")
                    return formatted_date
                    
            except Exception as e:
                print(f"Error formatting date: {e}")
                continue
    
    print("No filling date found")
    return None

def create_zip_file(delivery_number, output_folder):
    """
    Create a ZIP file of all split PDFs
    """
    zip_filename = f"{delivery_number}.zip"
    zip_path = Path(zip_filename)
    
    print(f"Creating ZIP file: {zip_filename}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pdf_file in output_folder.glob("*.pdf"):
            zipf.write(pdf_file, pdf_file.name)
            print(f"Added to ZIP: {pdf_file.name}")
    
    print(f"✓ ZIP file created: {zip_path}")
    return zip_path

def copy_to_sharepoint(zip_path, filling_date, delivery_number):
    """
    Copy ZIP file to SharePoint network drive in date-organized folder
    """
    try:
        # Check if SharePoint path is accessible
        if not SHAREPOINT_PATH.exists():
            print(f"ERROR: SharePoint path not accessible: {SHAREPOINT_PATH}")
            print("Make sure you're logged into the company network and have access to the folder")
            return False
        
        print(f"✓ SharePoint path accessible: {SHAREPOINT_PATH}")
        
        # Create date folder path
        date_folder = SHAREPOINT_PATH / filling_date
        
        # Check if date folder exists, create if not
        if not date_folder.exists():
            print(f"Creating date folder: {filling_date}")
            date_folder.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created date folder: {date_folder}")
        else:
            print(f"✓ Date folder already exists: {date_folder}")
        
        # Copy ZIP file to date folder
        destination_path = date_folder / zip_path.name
        
        print(f"Copying {zip_path.name} to SharePoint...")
        shutil.copy2(zip_path, destination_path)
        
        print(f"✓ Successfully copied to SharePoint:")
        print(f"  Location: {destination_path}")
        print(f"  Size: {destination_path.stat().st_size:,} bytes")
        
        return True
        
    except PermissionError as e:
        print(f"ERROR: Permission denied accessing SharePoint folder: {e}")
        print("Make sure you have write permissions to the SharePoint folder")
        return False
    except Exception as e:
        print(f"ERROR: Failed to copy to SharePoint: {e}")
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
    Use OCR to extract delivery number and filling date using hierarchical search
    """
    try:
        import pytesseract
        import pdf2image
        from PIL import Image
        
        print("Using OCR with hierarchical search...")
        
        images = pdf2image.convert_from_path(pdf_path)
        print(f"Converted {len(images)} pages to images")
        
        delivery_number = None
        filling_date = None
        
        for page_num, image in enumerate(images):
            print(f"\n--- OCR Processing Page {page_num + 1} ---")
            
            text = pytesseract.image_to_string(image)
            print(f"OCR extracted {len(text)} characters from page {page_num + 1}")
            
            if text and len(text) > 100:
                # Extract delivery number if not found yet
                if not delivery_number:
                    delivery_number = extract_delivery_number_hierarchical(text)
                
                # Extract filling date if not found yet
                if not filling_date:
                    filling_date = extract_filling_date(text)
                
                # Stop if we have both
                if delivery_number and filling_date:
                    break
            else:
                print(f"Insufficient text extracted from page {page_num + 1}")
        
        return delivery_number, filling_date
        
    except ImportError as e:
        print(f"OCR libraries not available: {e}")
        return extract_delivery_number_fallback(pdf_path)
    except Exception as e:
        print(f"OCR failed with error: {e}")
        return extract_delivery_number_fallback(pdf_path)

def extract_delivery_number_fallback(pdf_path):
    """
    Fallback method using PyPDF2 with hierarchical search
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            delivery_number = None
            filling_date = None
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text and len(text) > 100:
                        print(f"PyPDF2 extracted {len(text)} characters from page {page_num + 1}")
                        
                        if not delivery_number:
                            delivery_number = extract_delivery_number_hierarchical(text)
                        
                        if not filling_date:
                            filling_date = extract_filling_date(text)
                        
                        if delivery_number and filling_date:
                            break
                            
                except Exception as page_error:
                    print(f"Error processing page {page_num + 1}: {page_error}")
                    
            return delivery_number, filling_date
    
    except Exception as e:
        print(f"PyPDF2 fallback failed: {e}")
        return None, None

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
    Main function to process shipping PDF with SharePoint network drive integration
    """
    pdf_path = Path(pdf_path)
    base_output_folder = Path(base_output_folder)
    
    print(f"Processing: {pdf_path.name}")
    
    # Extract delivery number and filling date
    delivery_number, filling_date = extract_delivery_number_ocr(pdf_path)
    
    if not delivery_number:
        print("ERROR: Could not find valid delivery number")
        return False, None
    
    if not filling_date:
        print("WARNING: Could not find filling date, using current date")
        filling_date = datetime.now().strftime("%d.%m.%y")
    
    print(f"✓ VALIDATED delivery number: {delivery_number}")
    print(f"✓ EXTRACTED filling date: {filling_date}")
    
    # Create output folder
    delivery_folder = base_output_folder / delivery_number
    delivery_folder.mkdir(parents=True, exist_ok=True)
    print(f"Created folder: {delivery_folder}")
    
    # Split PDF into pages
    page_files = split_pdf_to_pages(pdf_path, delivery_folder, delivery_number)
    
    if page_files:
        print(f"\nSUCCESS: Created {len(page_files)} individual PDF files")
        
        # Create ZIP file
        zip_path = create_zip_file(delivery_number, delivery_folder)
        
        # Copy to SharePoint
        copy_success = copy_to_sharepoint(zip_path, filling_date, delivery_number)
        
        if copy_success:
            # Clean up local files
            print("Cleaning up local files...")
            try:
                # Delete ZIP file
                zip_path.unlink()
                print(f"✓ Deleted local ZIP: {zip_path}")
                
                # Delete output folder and contents
                for file in delivery_folder.glob("*"):
                    file.unlink()
                delivery_folder.rmdir()
                print(f"✓ Deleted output folder: {delivery_folder}")
                
                # Delete original PDF
                pdf_path.unlink()
                print(f"✓ Deleted original file: {pdf_path.name}")
                
            except Exception as e:
                print(f"Warning: Cleanup error: {e}")
        
        return copy_success, delivery_number
    else:
        print("ERROR: Failed to split PDF")
        return False, None

# Main execution
if __name__ == "__main__":
    print("=== SHAREPOINT NETWORK DRIVE PDF SPLITTER STARTING ===")
    print(f"SharePoint target path: {SHAREPOINT_PATH}")
    
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
        print(f"Processed delivery numbers: {processed_delivery_numbers}")
        print(f"Files copied to SharePoint: {SHAREPOINT_PATH}")
