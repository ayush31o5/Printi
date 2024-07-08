import pdfplumber
from docx import Document
import comtypes.client
import os

def count_pdf_pages(filepath):
    with pdfplumber.open(filepath) as pdf:
        return len(pdf.pages)

def count_docx_pages(filepath):
    doc = Document(filepath)
    return len(doc.paragraphs) // 30  # Placeholder for actual page count logic

def count_doc_pages(filepath):
    word = comtypes.client.CreateObject('Word.Application')
    doc = word.Documents.Open(filepath)
    new_filepath = filepath + 'x'
    doc.SaveAs(new_filepath, FileFormat=16)  # Save as .docx
    doc.Close()
    word.Quit()
    page_count = count_docx_pages(new_filepath)
    os.remove(new_filepath)
    return page_count

def count_txt_pages(filepath, lines_per_page=50):
    with open(filepath, 'r') as f:
        lines = f.readlines()
        return (len(lines) // lines_per_page) + 1
