import time
import socket
import asyncio
from pywifi import PyWiFi, const, Profile
from bleak import BleakClient, BleakScanner
from zeroconf import Zeroconf, ServiceBrowser

def connect_to_wifi_direct(ssid, auth_type, password):
    """
    Connects to a Wi-Fi Direct network using the provided SSID, auth_type, and password.
    Note: The auth_type parameter is currently not used in the connection logic.
    """
    try:
        wifi = PyWiFi()
        interfaces = wifi.interfaces()

        if not interfaces:
            raise Exception("No Wi-Fi interfaces found. Make sure Wi-Fi is enabled.")

        iface = interfaces[0]  # Select the first Wi-Fi interface

        # Disconnect any existing connections
        iface.disconnect()
        time.sleep(1)

        # Set up Wi-Fi Direct profile
        profile = Profile()
        profile.ssid = ssid
        profile.auth = const.AUTH_ALG_OPEN
        if password:
            profile.akm.append(const.AKM_TYPE_WPA2PSK)
        else:
            profile.akm.append(const.AKM_TYPE_NONE)
        profile.key = password if password else ''
        profile.cipher = const.CIPHER_TYPE_CCMP

        # Apply the connection profile
        iface.remove_all_network_profiles()
        temp_profile = iface.add_network_profile(profile)
        iface.connect(temp_profile)
        time.sleep(10)

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
                if info:
                    self.ip = socket.inet_ntoa(info.addresses[0])

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
