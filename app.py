import os
import hmac
import hashlib
import base64
from io import BytesIO
from dotenv import load_dotenv

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, jsonify,
    send_from_directory
)
import razorpay
import qrcode

from utils.wifi_direct import (
    generate_wifi_qr,
    discover_printer_ip
)
from utils.count_pages import count_pages
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

        printer_info = {
            "ssid": ssid,
            "password": password,
            "auth_type": auth_type,
            "bluetooth_mac": bluetooth_mac,
        }
        add_printer(printer_info)

        qr_base64 = generate_wifi_qr(ssid, auth_type, password)

        return render_template(
            "qr_code.html",
            qr_base64=qr_base64,
            redirect_url=url_for("connected"),
            **printer_info
        )

    return render_template("printer_setup_form.html")

@app.route("/connected")
def connected():
    return render_template("connected.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    printer_name = request.form.get("printer", "")
    os.makedirs("uploads", exist_ok=True)
    filepath = os.path.join("uploads", file.filename)
    file.save(filepath)

    num_pages = count_pages(filepath)
    amount = num_pages * 100

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

    filename = os.path.basename(order_data["filepath"])
    download_url = url_for("download_file", filename=filename, _external=True)

    return render_template(
        "confirmation.html",
        printer_name=order_data["printer_name"],
        num_pages=order_data["num_pages"],
        amount=order_data["amount"],
        download_url=download_url
    )

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory("uploads", filename, as_attachment=True)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        ssl_context="adhoc"
    )
