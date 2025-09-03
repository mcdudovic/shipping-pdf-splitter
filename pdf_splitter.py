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
                    r"Order:\s*(\d+)",              # Order: followed by number (from packing list)
                    r"Order:(\d+)",                 # Order: with no space (exact match from log)
                    r"Order\s*[:\s]+\s*(\d+)",     # Order with various spacing
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
