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
    The generated QR code now includes a URL with connection parameters.
    """
    if request.method == 'POST':
        ssid = request.form['ssid']
        password = request.form.get('password', '')
        auth_type = request.form['auth_type']
        bluetooth_mac = request.form.get('bluetooth_mac', '')

        # Build a URL to the connect_printer route with query parameters
        connect_url = url_for('connect_printer_route', _external=True,
                              ssid=ssid, auth_type=auth_type, password=password, bluetooth_mac=bluetooth_mac)

        # Generate the QR code with the URL as data
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(connect_url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Save printer info if needed
        printer_info = {
            'ssid': ssid,
            'password': password,
            'auth_type': auth_type,
            'bluetooth_mac': bluetooth_mac,
            'qr_code': qr_base64
        }
        add_printer(printer_info)

        # Pass the necessary parameters to the template along with the QR code
        return render_template(
            "qr_code.html",
            qr_base64=qr_base64,
            ssid=ssid,
            auth_type=auth_type,
            password=password,
            bluetooth_mac=bluetooth_mac
        )

    return render_template('printer_setup_form.html')


@app.route('/connect_printer', methods=['GET', 'POST'])
async def connect_printer_route():
    """
    Endpoint called when the QR code is scanned.
    - On GET: serves an auto‑connect page that auto‑submits connection data.
    - On POST: attempts a Wi‑Fi Direct connection automatically and saves the connected printer.
    """
    if request.method == 'POST':
        # Support both JSON and form submissions
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form
        ssid = data.get('ssid', '')
        auth_type = data.get('auth_type', '')
        password = data.get('password', '')
        bluetooth_mac = data.get('bluetooth_mac', '')

        result = connect_to_wifi_direct(ssid, auth_type, password)
        
        if result.get("status") == "success":
            # Store the connected printer identifier in the session.
            # Here, using SSID as a simple identifier. Modify as needed.
            session['connected_printer'] = ssid  
        return jsonify(result)
    else:
        return render_template(
            'auto_connect.html',
            ssid=request.args.get('ssid', ''),
            auth_type=request.args.get('auth_type', ''),
            password=request.args.get('password', ''),
            bluetooth_mac=request.args.get('bluetooth_mac', '')
        )


@app.route('/provide_paper')
def provide_paper_page():
    """
    Page for submitting printing options using the connected printer.
    """
    connected_printer = session.get('connected_printer')
    if not connected_printer:
        # If no printer is connected, redirect to the home page.
        return redirect(url_for('home'))
    return render_template('provide_paper.html', printer=connected_printer)


@app.route('/process_paper_submission', methods=['POST'])
def process_paper_submission():
    # Retrieve the printer from the form or session.
    printer = request.form.get('printer') or session.get('connected_printer')
    paper_count = int(request.form.get('paper_count'))
    
    # Additional printing options.
    print_option = request.form.get('print_option')
    paper_size = request.form.get('paper_size')
    color_option = request.form.get('color_option')
    
    if not printer or paper_count <= 0:
        return jsonify({"status": "failed", "error": "Invalid printer or paper count"}), 400

    # Example pricing logic (adjust multipliers based on options if needed).
    amount = paper_count * 100

    order = razorpay_client.order.create({
        'amount': amount,
        'currency': 'INR',
        'payment_capture': '1'
    })

    # Save all order data in the session.
    session['order_data'] = {
        'printer_name': printer,
        'num_pages': paper_count,
        'print_option': print_option,
        'paper_size': paper_size,
        'color_option': color_option,
        'amount': amount,
        'order_id': order['id']
        # If you add a file upload flow, include 'filepath' here.
    }

    return render_template(
        'payment.html',
        amount=amount,
        razorpay_key=os.getenv('RAZORPAY_KEY')
    )


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
        # If using a file-upload flow, print the file:
        if 'filepath' in order_data:
            send_to_printer(order_data['filepath'], order_data['printer_name'])
        # Otherwise, process the printing job as needed.
        return render_template(
            'confirmation.html',
            printer_name=order_data['printer_name'],
            num_pages=order_data['num_pages'],
            amount=order_data['amount']
        )
    else:
        return "Payment verification failed", 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
