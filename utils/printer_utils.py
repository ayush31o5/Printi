import os
import platform
import subprocess

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
        raise NotImplementedError("Printing is not supported on this platform.")
