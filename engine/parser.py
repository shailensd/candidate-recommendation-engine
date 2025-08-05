import PyPDF2
from docx import Document
import re
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file):
    """Extracts text from a PDF file using PyPDF2."""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Failed to read PDF: {e}")
        return ""

def extract_text_from_docx(file):
    """Extracts text from a DOCX file using python-docx."""
    try:
        doc = Document(file)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return text
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

    lines = text.split('\n')
    name = lines[0][:50] if lines else "Unknown Candidate"

    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    email = email_match.group() if email_match else "No email found"

    # Phone number pattern (supports many formats)
    phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phone_match = re.search(phone_pattern, text)
    phone = phone_match.group() if phone_match else "No phone found"

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "full_text": text
    }
