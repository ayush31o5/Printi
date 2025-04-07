Printi Project Documentation
=============================

Overview
--------
Printi is a web-based platform designed for printer shops that enables easy printer registration and print job submission through a QR code connection. The project leverages Wi-Fi Direct (and optionally Bluetooth) to connect users’ devices directly to printers. It also integrates Razorpay for secure payment processing and provides a streamlined printing workflow.

Key Features
------------
1. **Printer Registration & QR Code Generation:**
   - Register your printer by entering its Wi-Fi Direct details (SSID, password, security type) and optionally the Bluetooth MAC address.
   - A QR code is generated that embeds the connection details for an automatic connection process.

2. **Auto-Connect Flow:**
   - When a user scans the QR code, the app automatically initiates a Wi-Fi Direct connection to the printer.
   - The connection process is automated, so no manual “Connect” steps are required.

3. **Payment & Print Submission:**
   - Users can upload documents, and the system counts the pages.
   - Payments are processed via Razorpay.
   - Once payment is verified, the print job is sent to the registered printer.

4. **User-Friendly Interface:**
   - The interface uses a dark blue background with contrasting white (or black) text for readability.
   - Clear, step-by-step instructions are provided for both printer registration and the auto-connect process.

System Architecture
-------------------
- **Backend:**
  - Built with Python and Flask.
  - **Wi-Fi Direct & Bluetooth Utilities:** Located in the `utils/wifi_direct.py` module, which handles connections using libraries like pywifi and bleak.
  - **Payment Integration:** Razorpay is integrated to handle payments.
  - **Data Storage:** Printer registration details are stored using functions defined in the `database.py` module.
  - **Print Job Handling:** Document uploads, page counting, and job submissions are managed via dedicated modules (e.g., `utils/count_pages.py` and `utils/printer_utils.py`).

- **Frontend:**
  - HTML, CSS, and JavaScript are used.
  - The auto-connect page (e.g., `templates/auto_connect.html`) automatically triggers the connection process upon QR code scanning.

- **Deployment:**
  - The application runs on a Flask development server.
  - For production, it is recommended to use a production WSGI server (e.g., Gunicorn) behind a reverse proxy (e.g., Nginx) with SSL termination.

File Structure
--------------
Printi/
├── app.py                   # Main Flask application
├── database.py              # Database functions for printer registration
├── requirements.txt         # Python dependencies
├── run_app.sh               # Script to run the application
├── utils/
│   ├── wifi_direct.py       # Wi-Fi Direct and Bluetooth connection utilities
│   ├── count_pages.py       # Document page counting logic
│   └── printer_utils.py     # Functions to send documents to the printer
├── templates/
│   ├── home.html            # Home page with links and instructions
│   ├── printer_setup_form.html  # Form for printer registration
│   ├── auto_connect.html    # Auto-connect page that triggers the connection process
│   ├── qr_code.html         # Displays the generated QR code for printer connection
│   ├── provide_paper.html   # Page for paper submission
│   └── confirmation.html    # Confirmation page after successful print job submission
└── static/
    └── styles.css           # Custom CSS (dark blue background, contrasting text)

Detailed Printer Registration & Wi-Fi Direct Instructions
-----------------------------------------------------------
### How the Printer Registration Process Works

1. **Access the Printer Setup Page:**
   - Navigate to the “Add a Printer” page via the home page.
   - Fill in the required details:
     - **SSID:** The printer’s Wi-Fi network name.
     - **Password:** The network password (if applicable).
     - **Security Type (auth_type):** Typically WPA or WPA2.
     - **Bluetooth MAC (optional):** If the printer supports Bluetooth connectivity.

2. **QR Code Generation:**
   - After submission, the app generates a QR code that encodes the printer’s connection details.
   - The QR code is displayed for use by customers or users.

### Step-by-Step: Finding Wi-Fi Direct Information on Your Printer

1. **Locate the Printer’s Network Information:**
   - **Check the Printer’s Label:**
     - Many printers have a sticker on the back or bottom that displays the default Wi-Fi SSID (network name) and password.
   - **Refer to the Printer Manual:**
     - Look for sections titled “Wireless Setup,” “Wi-Fi Direct,” or “Network Settings.”
   - **Onboard Display/Menu:**
     - If your printer has an LCD screen or control panel, navigate to the **Settings** or **Network** menu.
     - Look for an option labeled **Wi-Fi Direct** or **Wireless LAN**.
     - The display should show the SSID and security details (e.g., WPA2).

2. **Verify Security Settings:**
   - **Security Type (WPA/WPA2):**
     - Most modern printers use WPA2-PSK. Confirm this on the printer’s network menu.
   - **Password/Passphrase:**
     - The password is usually printed on the device or provided in the documentation.
   - **Additional Details:**
     - Some printers may also display other technical details (e.g., encryption type such as CCMP), but the key information needed is the SSID, password, and security type.

3. **If You Can’t Find the Information:**
   - **Consult the Manufacturer’s Website:**
     - Search for support articles or download the user manual.
   - **Contact Technical Support:**
     - Reach out to the printer manufacturer’s support team for assistance.
   - **Ask the Network Administrator:**
     - In a printer shop setting, the network administrator may have the necessary details.

Deployment & Troubleshooting
-----------------------------
### Deployment Recommendations
- **Reverse Proxy:**
  - Use Nginx or Apache as a reverse proxy to handle HTTPS connections (SSL termination) and forward requests to your Flask app.
- **Production Server:**
  - Deploy the Flask app using a production WSGI server like Gunicorn.
- **DNS Settings:**
  - Ensure your domain (e.g., i4cinvention.in) correctly points to your server’s IP address.

### Common Issues & Solutions
- **Wi-Fi Interface Not Found:**
  - **Cause:** The app is running on a device without a Wi-Fi adapter (e.g., a cloud server).
  - **Solution:** Test on a device with an active Wi-Fi adapter (e.g., a laptop or Raspberry Pi) or simulate the Wi-Fi interface during development.
  
- **HTTPS vs. HTTP Mismatch:**
  - **Cause:** Clients attempting to connect via HTTPS to an HTTP server.
  - **Solution:** Set up SSL termination with a reverse proxy so that HTTPS connections are properly handled.

- **Connection Timeouts or Errors:**
  - **Cause:** Slow network responses or incorrect printer details.
  - **Solution:** Verify the Wi-Fi Direct settings and implement retry logic with clear error messages for users.

How to Use the Application
--------------------------
1. **Register Your Printer:**
   - Go to the “Add a Printer” page.
   - Enter the printer’s Wi-Fi Direct details (SSID, password, security type) and, optionally, Bluetooth details.
   - A QR code will be generated that encodes these details.

2. **Customer Interaction:**
   - A customer scans the QR code.
   - The auto-connect page loads on their device and automatically initiates a Wi-Fi Direct connection.
   - **Important:** Ensure the customer’s phone has Wi-Fi enabled (but do not manually join the printer’s Wi-Fi network; remain on mobile data).

3. **Print Job Submission:**
   - Customers upload their document.
   - The app counts the pages and processes payment via Razorpay.
   - After successful payment, the document is sent to the printer for printing.

Final Notes
-----------
- **UI/UX Improvements:**
  - The interface uses high-contrast colors (e.g., dark blue background with white or black text) for improved readability.
  - Clear instructions guide the user through every step of the process.
  
- **User Instructions:**
  - Detailed instructions are provided to help users locate the necessary Wi-Fi Direct details on their printer.
  - Troubleshooting tips and deployment recommendations are included for administrators.

