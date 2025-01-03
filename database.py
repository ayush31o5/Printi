from pymongo import MongoClient
from bson import ObjectId
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to MongoDB
try:
    client = MongoClient(os.getenv('MONGODB_URI', 'mongodb+srv://ayushsinghai3105:ayush12345@cluster0.yierv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'))
    db = client['printer_database']  # Use your database name
    logger.info("MongoDB connection successful!")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Printer collection
printer_collection = db['test']

def add_printer(printer_data):
    """Add a new printer to the database."""
    try:
        if not isinstance(printer_data, dict):
            raise ValueError("Printer data must be a dictionary.")
        
        # Required fields (you can adjust this to your needs)
        required_fields = ['ssid', 'password', 'auth_type', 'qr_code']
        for field in required_fields:
            if field not in printer_data:
                raise ValueError(f"Missing required field: {field}")
        
        result = printer_collection.insert_one(printer_data)
        logger.info(f"Printer added with ID: {result.inserted_id}")
        return {"status": "success", "message": "Printer added successfully.", "id": str(result.inserted_id)}
    except Exception as e:
        logger.error(f"Error adding printer: {e}")
        return {"status": "error", "message": str(e)}


def get_printer_by_id(printer_id):
    """Retrieve a printer by its ID."""
    try:
        if not ObjectId.is_valid(printer_id):
            raise ValueError("Invalid ObjectId format.")
        
        printer_id = ObjectId(printer_id)
        printer = printer_collection.find_one({'_id': printer_id})
        if not printer:
            raise ValueError("Printer not found.")
        
        logger.info(f"Printer retrieved: {printer}")
        return {"status": "success", "data": printer}
    except Exception as e:
        logger.error(f"Error retrieving printer by ID: {e}")
        return {"status": "error", "message": str(e)}

def get_all_printers():
    """Retrieve all printers from the database."""
    try:
        printers = list(printer_collection.find())
        logger.info(f"Retrieved {len(printers)} printers.")
        return {"status": "success", "data": printers}
    except Exception as e:
        logger.error(f"Error retrieving printers: {e}")
        return {"status": "error", "message": str(e)}
