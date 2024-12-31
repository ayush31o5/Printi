from pymongo import MongoClient
import os

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb+srv://ayushsinghai3105:QfTWVTn1RWD8Kji3@cluster0.yierv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'))
db = client['printer_database']  # Use your database name

# Printer collection
printer_collection = db['printers']

def add_printer(printer_data):
    """Add a new printer to the database."""
    printer_collection.insert_one(printer_data)

def get_printer_by_id(printer_id):
    """Retrieve a printer by its ID."""
    return printer_collection.find_one({'_id': printer_id})

def get_all_printers():
    """Retrieve all printers from the database."""
    return list(printer_collection.find())
