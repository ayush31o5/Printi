from flask import Flask, render_template, request, redirect, url_for, session
import razorpay
import qrcode
from io import BytesIO
import base64
from utils.count_pages import count_pages
from utils.printer_utils import get_printers, send_to_printer
from dotenv import load_dotenv
import os
import hmac
import hashlib

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
razorpay_client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY'), os.getenv('RAZORPAY_SECRET')))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add_printer', methods=['GET', 'POST'])
def printer_setup():
    if request.method == 'POST':
        ssid = request.form['ssid']
        password = request.form['password']
        auth_type = request.form['auth_type']

        wifi_info = f"WIFI:T:{auth_type};S:{ssid};P:{password};;"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(wifi_info)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return render_template('qr_code.html', qr_base64=qr_base64)

    return render_template('printer_setup_form.html')

@app.route('/connect_printer')
def index():
    printers = get_printers()
    return render_template('index.html', printers=printers)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    printer_name = request.form.get('printer')
    filepath = os.path.join('uploads', file.filename)
    file.save(filepath)

    num_pages = count_pages(filepath)
    amount = num_pages * 100  # 1 Rupee per page, Razorpay expects amount in paise

    order = razorpay_client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})

    session['order_data'] = {
        'filepath': filepath,
        'printer_name': printer_name,
        'num_pages': num_pages,
        'amount': amount,
        'order_id': order['id']
    }

    return render_template('payment.html', amount=amount, razorpay_key=os.getenv('RAZORPAY_KEY'))

@app.route('/verify', methods=['POST'])
def verify_payment():
    order_data = session.get('order_data')
    if not order_data:
        return redirect(url_for('index'))

    # Payment verification
    payment_id = request.form.get('razorpay_payment_id')
    order_id = order_data['order_id']
    signature = request.form.get('razorpay_signature')

    generated_signature = hmac.new(
        os.getenv('RAZORPAY_SECRET').encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()

    if generated_signature == signature:
        send_to_printer(order_data['filepath'], order_data['printer_name'])
        return render_template('confirmation.html',
                               printer_name=order_data['printer_name'],
                               num_pages=order_data['num_pages'],
                               amount=order_data['amount'])
    else:
        return "Payment verification failed", 400

if __name__ == '__main__':
    app.run(debug=True)
