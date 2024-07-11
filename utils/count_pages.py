import pdfplumber
from docx import Document
import comtypes.client

def count_pages(filepath):
    file_ext = filepath.rsplit('.', 1)[1].lower()
    if file_ext == 'pdf':
        return count_pdf_pages(filepath)
    elif file_ext in {'doc', 'docx'}:
        return count_doc_pages(filepath)
    elif file_ext == 'txt':
        return count_txt_pages(filepath)
    else:
        return None

def count_pdf_pages(filepath):
    try:
        with pdfplumber.open(filepath) as pdf:
            return len(pdf.pages)
    except Exception as e:
        print(e)
        return None

def count_doc_pages(filepath):
    try:
        doc = Document(filepath)
        return len(doc.paragraphs)
    except Exception as e:
        print(e)
        return None

def count_txt_pages(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            return len(lines) // 30 + 1  # assuming 30 lines per page
    except Exception as e:
        print(e)
        return None
