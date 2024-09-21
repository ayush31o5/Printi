import pdfplumber
from docx import Document

def count_pages(filepath):
    file_ext = filepath.rsplit('.', 1)[1].lower()
    if file_ext == 'pdf':
        return count_pdf_pages(filepath)
    elif file_ext in {'doc', 'docx'}:
        return count_doc_pages(filepath)
    elif file_ext == 'txt':
        return count_txt_pages(filepath)
    else:
        raise ValueError("Unsupported file type")

def count_pdf_pages(filepath):
    try:
        with pdfplumber.open(filepath) as pdf:
            return len(pdf.pages)
    except Exception as e:
        print(f"Error counting PDF pages: {e}")
        return 0

def count_doc_pages(filepath):
    try:
        doc = Document(filepath)
        return len(doc.paragraphs) // 30 + 1  # Assuming 30 paragraphs per page
    except Exception as e:
        print(f"Error counting DOC pages: {e}")
        return 0

def count_txt_pages(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            return len(lines) // 30 + 1  # Assuming 30 lines per page
    except Exception as e:
        print(f"Error counting TXT pages: {e}")
        return 0
