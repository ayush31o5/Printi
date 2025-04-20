import os
import platform
import subprocess
from bleak import BleakClient

# utils/printer_utils.py
import os
import platform
import subprocess
import socket

def get_printers():
    system = platform.system()
    if system == "Windows":
        import win32print
        return [printer[2] for printer in win32print.EnumPrinters(2)]
    elif system == "Linux":
        lines = subprocess.check_output(["lpstat", "-p"]).decode().splitlines()
        return [line.split(" ")[1] for line in lines if "printer" in line]
    else:
        raise NotImplementedError("Printing not supported on this platform.")

def send_raw_print(filepath, printer_ip, port=9100):
    """
    Sends the raw file bytes over JetDirect (TCP/9100).
    """
    try:
        with open(filepath, "rb") as f:
            data = f.read()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((printer_ip, port))
            s.sendall(data)

        return {"status": "success", "message": f"Sent {os.path.basename(filepath)} to {printer_ip}:{port}"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# (keep any Bluetooth‐printing helpers here if you need them)


async def connect_bluetooth_printer(mac_address):
    """
    Connects to a Bluetooth printer using BleakClient.
    """
    try:
        async with BleakClient(mac_address) as client:
            if await client.is_connected():
                print(f"Connected to Bluetooth printer with MAC address: {mac_address}")
            else:
                raise Exception(f"Failed to connect to Bluetooth printer with MAC address: {mac_address}")
    except Exception as e:
        raise Exception(f"An error occurred while connecting to Bluetooth printer: {e}")
