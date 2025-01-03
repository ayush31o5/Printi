from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import razorpay
import qrcode
from io import BytesIO
import base64
import os
import hmac
import hashlib
from dotenv import load_dotenv
from utils.wifi_direct import connect_to_wifi_direct, connect_to_bluetooth, find_bluetooth_mac_by_name
from database import add_printer
from utils.count_pages import count_pages
from utils.printer_utils import send_to_printer

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

razorpay_client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY'), os.getenv('RAZORPAY_SECRET')))

@app.route('/favicon.ico')
def favicon():
    return "", 204  # Serve blank favicon

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add_printer', methods=['GET', 'POST'])
def printer_setup():
    if request.method == 'POST':
        ssid = request.form['ssid']
        password = request.form.get('password', '')  
        auth_type = request.form['auth_type']
        bluetooth_mac = request.form.get('bluetooth_mac', '')

        connection_url = f"http://{request.host}/connect_printer?ssid={ssid}&auth_type={auth_type}&password={password}&bluetooth_mac={bluetooth_mac}"

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(connection_url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        printer_info = {'ssid': ssid, 'password': password, 'auth_type': auth_type, 'bluetooth_mac': bluetooth_mac, 'qr_code': qr_base64}
        add_printer(printer_info)

        return render_template("qr_code.html", qr_base64=qr_base64)

    return render_template('printer_setup_form.html')

@app.route('/connect_wifi', methods=['POST'])
def connect_wifi():
    data = request.json
    ssid = data.get('ssid')
    password = data.get('password')
    auth_type = data.get('auth_type')

    result = connect_to_wifi_direct(ssid, auth_type, password)
    return jsonify(result)

@app.route('/connect_bluetooth', methods=['POST'])
async def connect_bluetooth():
    bluetooth_name = request.json.get('bluetooth_mac')
    
    if not bluetooth_name:
        return jsonify({"status": "failed", "error": "Bluetooth device name is required."}), 400
    
    bluetooth_mac = find_bluetooth_mac_by_name(bluetooth_name)
    
    if not bluetooth_mac:
        return jsonify({"status": "failed", "error": f"Bluetooth device with name {bluetooth_name} not found."}), 404
    
    result = await connect_to_bluetooth(bluetooth_mac)
    return jsonify(result)

@app.route('/connect_printer')
def connect_printer():
    ssid = request.args.get('ssid', '')
    auth_type = request.args.get('auth_type', '')
    password = request.args.get('password', '')
    bluetooth_mac = request.args.get('bluetooth_mac', '')

    return render_template('index.html', ssid=ssid, auth_type=auth_type, password=password, bluetooth_mac=bluetooth_mac)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    printer_name = request.form.get('printer')
    filepath = os.path.join('uploads', file.filename)
    file.save(filepath)

    num_pages = count_pages(filepath)
    amount = num_pages * 100  

    order = razorpay_client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})

    session['order_data'] = {'filepath': filepath, 'printer_name': printer_name, 'num_pages': num_pages, 'amount': amount, 'order_id': order['id']}

    return render_template('payment.html', amount=amount, razorpay_key=os.getenv('RAZORPAY_KEY'))

@app.route('/verify', methods=['POST'])
def verify_payment():
    order_data = session.get('order_data')
    if not order_data:
        return redirect(url_for('index'))

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
        return render_template('confirmation.html', printer_name=order_data['printer_name'], num_pages=order_data['num_pages'], amount=order_data['amount'])
    else:
        return "Payment verification failed", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
