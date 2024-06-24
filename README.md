Introduction
The Printer Project Web Application allows users to upload documents and send them to a selected printer for printing. It includes functionality for counting the number of pages in various document formats and integrates with Razorpay for payment processing. The application is designed to be responsive, making it accessible from both desktop and mobile devices. 


Features
 Document Upload: Users can upload PDF, DOC, DOCX, and TXT files.  Printer Selection: Automatically lists available printers on the network.  Page Count: Automatically counts the number of pages in the uploaded document.  Payment Calculation: Calculates the amount to be paid based on the number of pages.  Razorpay Integration: Allows users to pay for their print jobs using Razorpay. 

 Responsive Design: Ensures the website is accessible from both desktop and mobile devices.  Connecting Printer: Printers can be connected through multiple ways such as local network, Bluetooth, and WiFi Direct. 

Document Upload and Printing
Upload Document: Go to the upload page and select a file to upload. 2. Select Printer: Choose a printer from the dropdown list. 3. Upload and Print: Click the "Upload and Print" button. The application will count the number of pages and redirect you to the payment page. Payment
Review Payment: Review the number of pages and the amount to be paid. 2. Pay Now: Click the "Pay Now" button to proceed with the payment via Razorpay. Payment Integration

Razorpay Integration
 The application uses Razorpay for processing payments.  The amount to be paid is calculated based on the number of pages in the document.  Payments are processed in paise, with 1 Rupee per page. Mobile Compatibility
 The application is designed to be responsive and works well on mobile devices.  Users can upload documents, select printers, and make payments directly from their mobile devices.

Code Structure
printer-project/
├── app.py
├── templates/
│ ├── index.html
│ ├── payment.html
├── static/
│ ├── index.css
│ ├── payment.css
├── uploads/
├── requirements.txt

Future Features
 Server Deployment: Upload the application to an online server for remote access.  Additional Print Features: Add features such as double-sided printing and color printing. 
 Automatic WiFi Direct Connectivity: Simplify the process of connecting printers via WiFi Direct. 
 QR Code for Printers: Generate QR codes for printers to facilitate easy connection and configuration. 

Additional Notes
 Error Handling: Ensure proper error handling is in place for file uploads, printing, and payment processing. 
 Security: Protect against common web vulnerabilities and ensure secure handling of payments. 
 Testing: Thoroughly test the application on different devices and browsers to ensure compatibility and usability.
