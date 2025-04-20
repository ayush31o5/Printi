# app.py

import os
import hmac
import hashlib
import base64
import qrcode
from io import BytesIO
from dotenv import load_dotenv

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, jsonify
)
import razorpay

from utils.wifi_direct import (
    connect_to_wifi_direct,
    discover_printer_ip,
)
from utils.count_pages import count_pages
from utils.printer_utils import send_raw_print
from database import add_printer

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.urandom(24)

razorpay_client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY"),
        os.getenv("RAZORPAY_SECRET")
    )
)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/add_printer", methods=["GET", "POST"])
def printer_setup():
    if request.method == "POST":
        ssid          = request.form["ssid"]
        password      = request.form.get("password", "")
        auth_type     = request.form["auth_type"]
        bluetooth_mac = request.form.get("bluetooth_mac", "")

        # Persist printer info
        printer_info = {
            "ssid": ssid,
            "password": password,
            "auth_type": auth_type,
            "bluetooth_mac": bluetooth_mac,
        }
        add_printer(printer_info)

        # Build the external URL for auto‑connect
        connect_url = url_for(
            "connect_printer",
            ssid=ssid,
            auth_type=auth_type,
            password=password,
            bluetooth_mac=bluetooth_mac,
            _external=True
        )

        # Generate QR code for that URL
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(connect_url)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        qr_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return render_template(
            "qr_code.html",
            qr_base64=qr_base64,
            connect_url=connect_url,
            **printer_info
        )

    return render_template("printer_setup_form.html")


@app.route("/connect_printer", methods=["GET", "POST"])
async def connect_printer():
    if request.method == "POST":
        data = request.get_json() or {}
        ssid      = data.get("ssid", "")
        auth_type = data.get("auth_type", "")
        password  = data.get("password", "")

        # 1) Attempt Wi‑Fi Direct connection
        result = connect_to_wifi_direct(ssid, auth_type, password)

        # 2) If successful, discover printer IP
        if result.get("status") == "success":
            printer_ip = discover_printer_ip()
            if printer_ip:
                result["printer_ip"] = printer_ip
            else:
                result = {
                    "status": "failed",
                    "error": "Could not discover printer IP."
                }

        return jsonify(result)

    # GET: serve the auto‑connect spinner
    return render_template(
        "auto_connect.html",
        ssid=request.args.get("ssid", ""),
        auth_type=request.args.get("auth_type", ""),
        password=request.args.get("password", ""),
        bluetooth_mac=request.args.get("bluetooth_mac", ""),
    )


@app.route("/provide_paper")
def provide_paper_page():
    return render_template("provide_paper.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    printer_name = request.form.get("printer", "")
    os.makedirs("uploads", exist_ok=True)
    filepath = os.path.join("uploads", file.filename)
    file.save(filepath)

    num_pages = count_pages(filepath)
    amount = num_pages * 100  # ₹100 per page

    order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1",
    })

    session["order_data"] = {
        "filepath": filepath,
        "printer_name": printer_name,
        "num_pages": num_pages,
        "amount": amount,
        "order_id": order["id"],
    }

    return render_template(
        "payment.html",
        amount=amount,
        razorpay_key=os.getenv("RAZORPAY_KEY")
    )


@app.route("/process_paper_submission", methods=["POST"])
def process_paper_submission():
    printer      = request.form.get("printer", "")
    paper_count  = int(request.form.get("paper_count", "0"))

    if not printer or paper_count <= 0:
        return jsonify({
            "status": "failed",
            "error": "Invalid printer or paper count"
        }), 400

    amount = paper_count * 100
    order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1",
    })

    # Preserve original file path from session
    filepath = session.get("order_data", {}).get("filepath", "")

    session["order_data"] = {
        "filepath": filepath,
        "printer_name": printer,
        "num_pages": paper_count,
        "amount": amount,
        "order_id": order["id"],
    }

    return render_template(
        "payment.html",
        amount=amount,
        razorpay_key=os.getenv("RAZORPAY_KEY")
    )


@app.route("/verify", methods=["POST"])
def verify():
    order_data = session.get("order_data")
    if not order_data:
        return redirect(url_for("home"))

    payment_id = request.form.get("razorpay_payment_id", "")
    order_id   = order_data["order_id"]
    signature  = request.form.get("razorpay_signature", "")

    generated_signature = hmac.new(
        os.getenv("RAZORPAY_SECRET").encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()

    if generated_signature != signature:
        return "Payment verification failed", 400

    # Send to printer
    printer_ip = discover_printer_ip()
    if not printer_ip:
        return "Printer IP not found; cannot send job.", 500

    send_result = send_raw_print(
        order_data["filepath"],
        printer_ip
    )

    return render_template(
        "confirmation.html",
        printer_name=order_data["printer_name"],
        num_pages=order_data["num_pages"],
        amount=order_data["amount"],
        send_result=send_result
    )


if __name__ == "__main__":
    # Run with HTTPS so that QR-scanned clients using HTTPS won't error
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        ssl_context="adhoc"
    )
