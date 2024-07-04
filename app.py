from flask import Flask, request, render_template, redirect, url_for, jsonify
import win32print
import razorpay
from models.document_model import DocumentModel

app = Flask(__name__)

# Razorpay client setup (replace with your Razorpay credentials)
razorpay_client = razorpay.Client(auth=("YOUR_RAZORPAY_KEY", "YOUR_RAZORPAY_SECRET"))

def get_printers():
    printers = []
    for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
        printers.append(printer[2])
    return printers

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
    if file and DocumentModel.allowed_file(file.filename):
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        num_pages = DocumentModel.count_pages(file, file_ext)

        printer_name = request.form.get('printer')
        
        try:
            file.seek(0)
            send_to_printer(file, printer_name)
        except Exception as e:
            return f"Error sending file to printer: {e}"
        
        amount = num_pages * 100  # 1 Rupee per page, Razorpay expects amount in paise
        return redirect(url_for('payment', amount=amount, printer_name=printer_name, num_pages=num_pages))
    else:
        return "File type not allowed"

@app.route('/payment/<int:amount>')
def payment(amount):
    printer_name = request.args.get('printer_name')
    num_pages = request.args.get('num_pages')
    return render_template('payment.html', amount=amount, printer_name=printer_name, num_pages=num_pages)

@app.route('/create_order', methods=['POST'])
def create_order():
    amount = request.form['amount']
    order = razorpay_client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})
    return jsonify(order)

def send_to_printer(file, printer_name):
    hPrinter = win32print.OpenPrinter(printer_name)
    try:
        hJob = win32print.StartDocPrinter(hPrinter, 1, ("Print Job", None, "RAW"))
        win32print.StartPagePrinter(hPrinter)
        raw_data = file.read()
        win32print.WritePrinter(hPrinter, raw_data)
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
    finally:
        win32print.ClosePrinter(hPrinter)

if __name__ == '__main__':
    app.run(debug=True)
