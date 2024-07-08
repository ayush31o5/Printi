from flask import Flask, request, render_template, redirect, url_for, jsonify, session
import os
import win32print
from werkzeug.utils import secure_filename
import razorpay
from page_counter import count_pdf_pages, count_docx_pages, count_doc_pages, count_txt_pages
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'bNgJt7zuJCgxXkcSO2oROchC'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Razorpay client setup (fetch from environment variables)
razorpay_key = os.getenv('RAZORPAY_KEY')
razorpay_secret = os.getenv('RAZORPAY_SECRET')
print(f'Razorpay Key: {razorpay_key}')  # Debug statement to print the key
print(f'Razorpay Secret: {razorpay_secret}')  # Debug statement to print the secret

razorpay_client = razorpay.Client(auth=(razorpay_key, razorpay_secret))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_printers():
    try:
        printers = []
        for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
            printers.append(printer[2])
        return printers
    except Exception as e:
        print(f"Error retrieving printers: {e}")
        return []

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
        
        amount = num_pages * 100  # 1 Rupee per page, Razorpay expects amount in paise
        
        # Create order in Razorpay
        order = razorpay_client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})
        
        # Save file path and other details to session
        order_data = {
            'filepath': filepath,
            'printer_name': printer_name,
            'num_pages': num_pages,
            'amount': amount,
            'order_id': order['id']
        }
        session['order_data'] = order_data
        
        return render_template('payment.html', amount=amount, order_id=order['id'], printer_name=printer_name, num_pages=num_pages)
    else:
        return "File type not allowed"

@app.route('/create_order', methods=['POST'])
def create_order():
    amount = request.form['amount']
    order = razorpay_client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})
    return jsonify(order)

@app.route('/payment_success', methods=['POST'])
def payment_success():
    order_data = session.get('order_data')
    if not order_data:
        return "Order data not found", 400

    payment_id = request.form['razorpay_payment_id']
    order_id = request.form['razorpay_order_id']
    signature = request.form['razorpay_signature']

    # Verify payment signature
    params_dict = {
        'razorpay_order_id': order_id,
        'razorpay_payment_id': payment_id,
        'razorpay_signature': signature
    }

    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
    except razorpay.errors.SignatureVerificationError:
        return "Payment verification failed", 400

    # Send document to printer
    try:
        send_to_printer(order_data['filepath'], order_data['printer_name'])
        os.remove(order_data['filepath'])
    except Exception as e:
        return f"Error sending file to printer: {e}"

    return render_template('confirmation.html', printer_name=order_data['printer_name'], num_pages=order_data['num_pages'], amount=order_data['amount'])

def send_to_printer(filepath, printer_name):
    try:
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
    except Exception as e:
        raise RuntimeError(f"Could not print the document. Error: {e}")

if __name__ == '__main__':
    app.run(debug=True)
