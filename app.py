from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import razorpay
import qrcode
from io import BytesIO
import base64
import os
import hmac
import hashlib
from dotenv import load_dotenv
from utils.wifi_direct import connect_to_wifi_direct, connect_to_bluetooth, discover_printer_ip, find_bluetooth_mac_by_name
from database import add_printer
from utils.count_pages import count_pages
from utils.printer_utils import send_to_printer
import asyncio

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

razorpay_client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY'), os.getenv('RAZORPAY_SECRET')))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add_printer', methods=['GET', 'POST'])
def printer_setup():
    """
    Registers a printer by saving its connection details and generating a QR code.
    The generated QR code includes SSID, auth_type, password, and (optionally) Bluetooth MAC.
    """
    if request.method == 'POST':
        ssid = request.form['ssid']
        password = request.form.get('password', '')
        auth_type = request.form['auth_type']
        bluetooth_mac = request.form.get('bluetooth_mac', '')

        # Generate connection URL (which will auto-connect without extra user choice)
        connection_url = f"http://{request.host}/connect_printer?ssid={ssid}&auth_type={auth_type}&password={password}&bluetooth_mac={bluetooth_mac}"

        # Generate QR code for the connection URL
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(connection_url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        printer_info = {
            'ssid': ssid,
            'password': password,
            'auth_type': auth_type,
            'bluetooth_mac': bluetooth_mac,
            'qr_code': qr_base64
        }
        add_printer(printer_info)

        return render_template("qr_code.html", qr_base64=qr_base64)

    return render_template('printer_setup_form.html')

@app.route('/connect_printer', methods=['GET', 'POST'])
async def connect_printer_route():
    """
    When the QR code is scanned, this endpoint is loaded.
    - On GET, it serves an auto‑connect page that immediately posts connection data.
    - On POST, it automatically attempts a Wi‑Fi Direct connection.
    """
    if request.method == 'POST':
        # Data is received as JSON from the auto_connect page.
        data = request.get_json() or {}
        ssid = data.get('ssid', '')
        auth_type = data.get('auth_type', '')
        password = data.get('password', '')
        bluetooth_mac = data.get('bluetooth_mac', '')

        # For auto-connect, we assume Wi-Fi Direct (Bluetooth option can be added later)
        result = connect_to_wifi_direct(ssid, auth_type, password)
        # Optionally, you could trigger Bluetooth if needed:
        # if bluetooth_mac:
        #     result = await connect_to_bluetooth(bluetooth_mac)
        return jsonify(result)
    else:
        # GET request: render the auto‑connect page with the parameters from the QR URL.
        return render_template(
            'auto_connect.html',
            ssid=request.args.get('ssid', ''),
            auth_type=request.args.get('auth_type', ''),
            password=request.args.get('password', ''),
            bluetooth_mac=request.args.get('bluetooth_mac', '')
        )

@app.route('/provide_paper')
def provide_paper_page():
    return render_template('provide_paper.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    printer_name = request.form.get('printer')
    filepath = os.path.join('uploads', file.filename)
    file.save(filepath)

    num_pages = count_pages(filepath)
    amount = num_pages * 100  # Example pricing logic

    order = razorpay_client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})

    session['order_data'] = {
        'filepath': filepath,
        'printer_name': printer_name,
        'num_pages': num_pages,
        'amount': amount,
        'order_id': order['id']
    }

    return render_template('payment.html', amount=amount, razorpay_key=os.getenv('RAZORPAY_KEY'))

@app.route('/process_paper_submission', methods=['POST'])
def process_paper_submission():
    printer = request.form.get('printer')
    paper_count = int(request.form.get('paper_count'))

    if not printer or paper_count <= 0:
        return jsonify({"status": "failed", "error": "Invalid printer or paper count"}), 400

    amount = paper_count * 100

    order = razorpay_client.order.create({
        'amount': amount,
        'currency': 'INR',
        'payment_capture': '1'
    })

    session['order_data'] = {
        'printer_name': printer,
        'num_pages': paper_count,
        'amount': amount,
        'order_id': order['id']
    }

    return render_template('payment.html', amount=amount, razorpay_key=os.getenv('RAZORPAY_KEY'))

@app.route('/verify', methods=['POST'])
def verify_payment():
    order_data = session.get('order_data')
    if not order_data:
        return redirect(url_for('home'))

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
        return render_template(
            'confirmation.html',
            printer_name=order_data['printer_name'],
            num_pages=order_data['num_pages'],
            amount=order_data['amount']
        )
    else:
        return "Payment verification failed", 400

if __name__ == '__main__':
    # In production, run behind a proper WSGI server (e.g., Gunicorn) with a reverse proxy (e.g., Nginx) to handle SSL.
    app.run(host='0.0.0.0', port=5000, debug=True)
