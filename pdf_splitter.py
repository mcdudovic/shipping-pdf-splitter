import PyPDF2
import re
import os
from pathlib import Path
import glob

def extract_delivery_number(pdf_path):
    """
    Extract the 10-digit delivery number starting with '88' from the PDF
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"PDF has {len(pdf_reader.pages)} pages")
            
            # Search through all pages for the delivery number
            for page_num, page in enumerate(pdf_reader.pages):
                print(f"\n--- Processing Page {page_num + 1} ---")
                
                try:
                    text = page.extract_text()
                    print(f"Extracted {len(text)} characters from page {page_num + 1}")
                    
                    # Show first 500 characters of extracted text for debugging
                    if text:
                        print(f"First 500 chars: {repr(text[:500])}")
                        
                        # Look for 10-digit number starting with 88
                        delivery_numbers = re.findall(r'\b88\d{8}\b', text)
                        
                        if delivery_numbers:
                            print(f"Found delivery numbers on page {page_num + 1}: {delivery_numbers}")
                            return delivery_numbers[0]  # Return first match
                        
                        # Also try to find it with spaces or other separators
                        spaced_numbers = re.findall(r'\b88[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d[\s\-\.]*\d\b', text)
                        if spaced_numbers:
                            # Remove spaces and separators
                            clean_number = re.sub(r'[\s\-\.]', '', spaced_numbers[0])
                            if len(clean_number) == 10 and clean_number.startswith('88'):
                                print(f"Found spaced delivery number on page {page_num + 1}: {clean_number}")
                                return clean_number
                        
                        # Try looking for the number as separate digits
                        digit_pattern = re.findall(r'8[\s]*8[\s]*\d[\s]*\d[\s]*\d[\s]*\d[\s]*\d[\s]*\d[\s]*\d[\s]*\d', text)
                        if digit_pattern:
                            clean_number = re.sub(r'\s', '', digit_pattern[0])
                            if len(clean_number) == 10:
                                print(f"Found digit-separated delivery number on page {page_num + 1}: {clean_number}")
                                return clean_number
                                
                    else:
                        print(f"No text extracted from page {page_num + 1}")
                        
                except Exception as page_error:
                    print(f"Error processing page {page_num + 1}: {page_error}")
    
    except Exception as e:
        print(f"Error reading PDF: {e}")
    
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
    1. Extract delivery number
    2. Create folder named after delivery number
    3. Split PDF into individual pages
    """
    pdf_path = Path(pdf_path)
    base_output_folder = Path(base_output_folder)
    
    print(f"Processing: {pdf_path.name}")
    
    # Step 1: Extract delivery number
    delivery_number = extract_delivery_number(pdf_path)
    
    if not delivery_number:
        print("ERROR: Could not find delivery number (10-digit starting with 88)")
        print("This might be because:")
        print("1. The PDF text is in image format (scanned)")
        print("2. The number format is different than expected")
        print("3. The text extraction isn't working properly")
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
    print("=== PDF Splitter Starting ===")
    
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
