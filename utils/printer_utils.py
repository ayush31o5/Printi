import os
import platform
import subprocess
from bleak import BleakClient

def get_printers():
    system = platform.system()
    
    if system == "Windows":
        import win32print
        printers = [printer[2] for printer in win32print.EnumPrinters(2)]
    elif system == "Linux":
        printers = subprocess.check_output(["lpstat", "-p"]).decode().splitlines()
        printers = [line.split(' ')[1] for line in printers if "printer" in line]
    else:
        raise NotImplementedError("Printing is not supported on this platform.")
    
    return printers

def send_to_printer(filepath, printer_name):
    system = platform.system()
    
    if system == "Windows":
        import win32print
        import win32api
        try:
            win32print.SetDefaultPrinter(printer_name)
            win32api.ShellExecute(0, "print", filepath, None, ".", 0)
        except Exception as e:
            raise RuntimeError(f"Failed to print document on Windows: {e}")
    
    elif system == "Linux":
        try:
            command = ['lp', '-d', printer_name, filepath]
            subprocess.run(command, check=True)
        except Exception as e:
            raise RuntimeError(f"Failed to print document on Linux: {e}")
    else:
        raise Exception("Unsupported platform for printing.")

async def connect_bluetooth_printer(mac_address):
    async with BleakClient(mac_address) as client:
        if await client.is_connected():
            print(f"Connected to {mac_address}")
        else:
            raise Exception(f"Failed to connect to Bluetooth device {mac_address}")
