import time
import socket
import asyncio
from pywifi import PyWiFi, const, Profile
from bleak import BleakClient
from zeroconf import Zeroconf, ServiceBrowser

def connect_to_wifi_direct(ssid, auth_type=None, password=None):
    try:
        # Initialize Wi-Fi interface
        wifi = PyWiFi()
        iface = wifi.interfaces()[0]

        # Disconnect any existing connections
        iface.disconnect()
        time.sleep(1)

        # Set up the Wi-Fi Direct connection profile
        profile = Profile()
        profile.ssid = ssid
        if auth_type and auth_type.lower() == "wpa2" and password:
            profile.auth = const.AUTH_ALG_OPEN
            profile.akm.append(const.AKM_TYPE_WPA2PSK)
            profile.key = password
        else:
            profile.auth = const.AUTH_ALG_OPEN
            profile.akm.append(const.AKM_TYPE_NONE)
        profile.cipher = const.CIPHER_TYPE_CCMP

        # Apply the connection profile
        iface.remove_all_network_profiles()
        temp_profile = iface.add_network_profile(profile)

        # Connect to the network
        iface.connect(temp_profile)
        time.sleep(10)  # Allow time for the connection to establish

        if iface.status() == const.IFACE_CONNECTED:
            printer_ip = discover_printer_ip()
            if not printer_ip:
                raise Exception("Failed to discover printer IP address.")
            return {"status": "success", "printer_ip": printer_ip}
        else:
            raise Exception("Wi-Fi Direct connection failed. Please check the credentials or SSID.")

    except Exception as e:
        return {"status": "failed", "error": str(e)}

# Discover Printer IP using Zeroconf
def discover_printer_ip():
    try:
        class PrinterListener:
            def __init__(self):
                self.ip = None

            def add_service(self, zeroconf, type, name):
                info = zeroconf.get_service_info(type, name)
                if info:
                    self.ip = socket.inet_ntoa(info.addresses[0])

        zc = Zeroconf()
        listener = PrinterListener()
        ServiceBrowser(zc, "_http._tcp.local.", listener)

        time.sleep(5)  # Wait for discovery
        zc.close()
        return listener.ip
    except Exception as e:
        print(f"Error discovering printer IP: {e}")
        return None

# Asynchronous function to connect to Bluetooth
async def connect_to_bluetooth_asyn(bluetooth_mac):
    try:
        async with BleakClient(bluetooth_mac) as client:
            is_connected = await client.is_connected()
            if is_connected:
                return {"status": "success", "message": f"Connected to Bluetooth device {bluetooth_mac}."}
            else:
                return {"status": "failed", "error": f"Failed to connect to Bluetooth device {bluetooth_mac}."}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# Corrected function to run asynchronous Bluetooth connection task
def connect_to_bluetooth(bluetooth_mac):
    task = connect_to_bluetooth_asyn(bluetooth_mac)
    return asyncio.run_coroutine_threadsafe(task, asyncio.get_event_loop()).result()

# Function to find Bluetooth MAC by device name
async def find_bluetooth_mac_by_name(bluetooth_name):
    try:
        devices = await discover(timeout=8)
        
        for device in devices:
            if bluetooth_name.lower() in device.name.lower():
                return device.address
        raise Exception(f"Bluetooth device with name '{bluetooth_name}' not found.")
    except Exception:
        return None

# Main function to handle Wi-Fi Direct and Bluetooth connection
def connect_printer(ssid, auth_type, password, bluetooth_name):
    wifi_response = connect_to_wifi_direct(ssid, auth_type, password)
    if wifi_response['status'] == 'success':
        print("Successfully connected to Wi-Fi Direct")
        printer_ip = wifi_response['printer_ip']
        print(f"Printer IP: {printer_ip}")

        # Find Bluetooth MAC using the printer's name
        bluetooth_mac = asyncio.run(find_bluetooth_mac_by_name(bluetooth_name))
        if bluetooth_mac:
            print(f"Connecting to Bluetooth device: {bluetooth_mac}")
            bluetooth_response = connect_to_bluetooth(bluetooth_mac)
            print(bluetooth_response)
        else:
            print(f"Bluetooth device '{bluetooth_name}' not found.")
    else:
        print(f"Failed to connect to Wi-Fi Direct: {wifi_response['error']}")

