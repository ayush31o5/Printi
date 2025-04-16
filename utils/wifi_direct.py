import time
import socket
import asyncio
from pywifi import PyWiFi, const, Profile
from bleak import BleakClient, BleakScanner
from zeroconf import Zeroconf, ServiceBrowser

def connect_to_wifi_direct(ssid, auth_type, password):
    """
    Connects to a Wi-Fi Direct network using provided SSID, auth_type, and password.
    """
    try:
        wifi = PyWiFi()
        interfaces = wifi.interfaces()
        if not interfaces:
            raise Exception("No Wi-Fi interfaces found. Make sure Wi-Fi is enabled.")
        iface = interfaces[0]
        iface.disconnect()
        time.sleep(1)
        
        profile = Profile()
        profile.ssid = ssid
        profile.auth = const.AUTH_ALG_OPEN
        
        # Use the auth_type parameter to determine the AKM and key.
        if auth_type.upper() == "WPA2":
            if not password:
                raise Exception("Password is required for WPA2 authentication.")
            profile.akm.append(const.AKM_TYPE_WPA2PSK)
            profile.key = password
        elif auth_type.upper() == "OPEN":
            profile.akm.append(const.AKM_TYPE_NONE)
            profile.key = ''
        else:
            raise Exception(f"Unsupported auth_type: {auth_type}")
            
        profile.cipher = const.CIPHER_TYPE_CCMP

        iface.remove_all_network_profiles()
        temp_profile = iface.add_network_profile(profile)
        iface.connect(temp_profile)
        time.sleep(10)  # Allow time for connection attempt
        if iface.status() == const.IFACE_CONNECTED:
            return {"status": "success", "message": "Connected to Wi-Fi Direct"}
        else:
            raise Exception("Wi-Fi Direct connection failed. Check SSID and password.")
    except Exception as e:
        return {"status": "failed", "error": str(e)}

async def connect_to_bluetooth_async(bluetooth_mac):
    try:
        async with BleakClient(bluetooth_mac) as client:
            is_connected = await client.is_connected()
            if is_connected:
                return {"status": "success", "message": f"Connected to Bluetooth device {bluetooth_mac}."}
            else:
                return {"status": "failed", "error": f"Failed to connect to Bluetooth device {bluetooth_mac}."}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def connect_to_bluetooth(bluetooth_mac):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(connect_to_bluetooth_async(bluetooth_mac))
        loop.close()
        return result
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def discover_printer_ip():
    try:
        class PrinterListener:
            def __init__(self):
                self.ip = None

            def add_service(self, zeroconf, service_type, name):
                info = zeroconf.get_service_info(service_type, name)
                if info and info.addresses:
                    self.ip = socket.inet_ntoa(info.addresses[0])
                    
            # Optionally, you can add update_service and remove_service methods if needed.
            
        zc = Zeroconf()
        listener = PrinterListener()
        ServiceBrowser(zc, "_http._tcp.local.", listener)
        time.sleep(5)
        zc.close()
        return listener.ip
    except Exception as e:
        return None

async def find_bluetooth_mac_by_name(bluetooth_name):
    try:
        devices = await BleakScanner.discover(timeout=8)
        for device in devices:
            if bluetooth_name.lower() in device.name.lower():
                return device.address
        raise Exception(f"Bluetooth device with name '{bluetooth_name}' not found.")
    except Exception as e:
        return None
