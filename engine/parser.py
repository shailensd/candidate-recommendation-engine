import pdfplumber
from docx import Document
import re
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file):
    """Extracts text from a PDF file using pdfplumber."""
    try:
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        logger.error(f"Failed to read PDF with pdfplumber: {e}")
        return ""

def extract_text_from_docx(file):
    """Extracts text from a DOCX file using python-docx."""
    try:
        doc = Document(file)
        text_parts = []
        
        # Extract text from paragraphs
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                text_parts.append(text)
        
        # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text = cell.text.strip()
                    if text:
                        text_parts.append(text)
        
        # Join all text parts
        full_text = "\n".join(text_parts)
        return full_text
    except Exception as e:
        logger.error(f"Failed to read DOCX: {e}")
        return ""

def clean_text(text):
    """Cleans and normalizes resume text."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)  # remove excessive whitespace
    text = re.sub(r'[^\w\s\.\,\!\?\-\+\=\&\|\:\;\(\)\[\]\{\}]', '', text)  # remove unwanted characters
    return text.strip()

def extract_candidate_info(text):
    """Extracts basic name, email, and phone info from resume text."""
    if not text:
        return {
            "name": "Unknown Candidate",
            "email": "No email found",
            "phone": "No phone found",
            "full_text": ""
        }

    # Clean the text first
    text = text.strip()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Find the first non-empty line as name
    name = "Unknown Candidate"
    for line in lines:
        if line and not line.startswith(('http', 'www', '@')) and len(line) < 100:
            # Skip obvious non-name lines
            if any(skip in line.lower() for skip in ['phone', 'email', 'address', 'experience', 'education', 'skills']):
                continue
            # Check if it looks like a name (contains letters, spaces, hyphens, apostrophes)
            if re.match(r'^[A-Za-z\s\-\.\']+$', line) and len(line.split()) <= 4:
                # For all-caps lines, check if it looks like a name (2-4 words) vs section header (1 word)
                if line.isupper():
                    words = line.split()
                    if 2 <= len(words) <= 4:  # Likely a name (e.g., "JOHN DOE")
                        name = line
                        break
                    elif len(words) == 1:  # Likely a section header (e.g., "EXPERIENCE")
                        continue
                else:
                    # Not all caps, treat as normal name
                    name = line
                    break

    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    email = email_match.group() if email_match else "No email found"

    # Phone number pattern (supports many formats including international)
    phone_patterns = [
        r'\(\d{3}\)\s*\d{3}\s*[-.]?\s*\d{4}',  # (408) 627 - 2229
        r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # Standard formats
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 408-627-2229
        r'\d{10}',  # 4086272229
        r'\+?\d{1,3}[-.\s]?\d{1,2}[-.\s]?\d{1,2}[-.\s]?\d{1,2}[-.\s]?\d{1,2}',  # International formats like +33-1-23-45-67-89
        r'\+?\d{1,3}[-.\s]?\d{5}[-.\s]?\d{5}',  # Indian format like +91-98765-43210
        r'\+?\d{1,3}[-.\s]?\d{1}[-.\s]?\d{8}',  # Dutch format like +31-6-12345678
    ]
    
    phone = "No phone found"
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            phone = phone_match.group()
            break

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "full_text": text
    }