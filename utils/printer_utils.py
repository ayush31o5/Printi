import os

def get_printers():
    import win32print
    printers = [printer[2] for printer in win32print.EnumPrinters(2)]
    return printers

def send_to_printer(filepath, printer_name):
    import win32print
    import win32api
    try:
        win32print.SetDefaultPrinter(printer_name)
        win32api.ShellExecute(0, "print", filepath, None, ".", 0)
    except Exception as e:
        raise RuntimeError("Failed to print document: " + str(e))
