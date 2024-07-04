import pdfplumber
from docx import Document
import comtypes.client
import io

class DocumentModel:
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in DocumentModel.ALLOWED_EXTENSIONS

    @staticmethod
    def count_pdf_pages(file):
        with pdfplumber.open(file) as pdf:
            return len(pdf.pages)

    @staticmethod
    def count_docx_pages(file):
        doc = Document(file)
        return len(doc.paragraphs) // 30  # Placeholder for actual page count logic

    @staticmethod
    def count_doc_pages(file):
        word = comtypes.client.CreateObject('Word.Application')
        doc = word.Documents.Open(file)
        new_file = io.BytesIO()
        doc.SaveAs(new_file, FileFormat=16)  # Save as .docx
        doc.Close()
        word.Quit()
        new_file.seek(0)
        return DocumentModel.count_docx_pages(new_file)

    @staticmethod
    def count_txt_pages(file, lines_per_page=50):
        lines = file.readlines()
        return (len(lines) // lines_per_page) + 1

    @staticmethod
    def count_pages(file, file_ext):
        if file_ext == 'pdf':
            return DocumentModel.count_pdf_pages(file)
        elif file_ext == 'docx':
            return DocumentModel.count_docx_pages(file)
        elif file_ext == 'doc':
            return DocumentModel.count_doc_pages(file)
        elif file_ext == 'txt':
            return DocumentModel.count_txt_pages(file)
        else:
            return 'Unknown format'
