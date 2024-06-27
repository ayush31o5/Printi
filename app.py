from flask import Flask, request, render_template, redirect, url_for, jsonify
import os
import win32print
from werkzeug.utils import secure_filename
import pdfplumber
from docx import Document
import comtypes.client
import razorpay

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Razorpay client setup (replace with your Razorpay credentials)
razorpay_client = razorpay.Client(auth=("YOUR_RAZORPAY_KEY", "YOUR_RAZORPAY_SECRET"))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_printers():
    printers = []
    for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
        printers.append(printer[2])
    return printers

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

@app.route('/')
def index():
    printers = get_printers()
    return render_template('index.html', printers=printers)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        file_ext = filename.rsplit('.', 1)[1].lower()
        if file_ext == 'pdf':
            num_pages = count_pdf_pages(filepath)
        elif file_ext == 'docx':
            num_pages = count_docx_pages(filepath)
        elif file_ext == 'doc':
            num_pages = count_doc_pages(filepath)
        elif file_ext == 'txt':
            num_pages = count_txt_pages(filepath)
        else:
            num_pages = 'Unknown format'

        printer_name = request.form.get('printer')
        
        try:
            send_to_printer(filepath, printer_name)
            os.remove(filepath)
        except Exception as e:
            return f"Error sending file to printer: {e}"
        
        amount = num_pages * 100  # 1 Rupee per page, Razorpay expects amount in paise
        return redirect(url_for('payment', amount=amount))
    else:
        return "File type not allowed"

@app.route('/payment/<int:amount>/<string:printer_name>/<int:num_pages>')
def payment(amount, printer_name, num_pages):
    return render_template('payment.html', amount=amount, printer_name=printer_name, num_pages=num_pages)


@app.route('/create_order', methods=['POST'])
def create_order():
    amount = request.form['amount']
    order = razorpay_client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})
    return jsonify(order)

def send_to_printer(filepath, printer_name):
    hPrinter = win32print.OpenPrinter(printer_name)
    try:
        hJob = win32print.StartDocPrinter(hPrinter, 1, ("Print Job", None, "RAW"))
        win32print.StartPagePrinter(hPrinter)
        with open(filepath, "rb") as f:
            raw_data = f.read()
            win32print.WritePrinter(hPrinter, raw_data)
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
    finally:
        win32print.ClosePrinter(hPrinter)

if __name__ == '__main__':
    app.run(debug=True)
