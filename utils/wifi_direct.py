import time
import socket
import asyncio
from pywifi import PyWiFi, const, Profile
from bleak import BleakClient
from zeroconf import Zeroconf, ServiceBrowser

def connect_to_wifi_direct(ssid, password):
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
        profile.akm.append(const.AKM_TYPE_WPA2PSK) if password else profile.akm.append(const.AKM_TYPE_NONE)
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

        time.sleep(5)
        zc.close()
        return listener.ip
    except Exception as e:
        return None

def connect_printer(ssid, password, bluetooth_mac):
    wifi_response = connect_to_wifi_direct(ssid, password)
    if wifi_response['status'] == 'success':
        print("✅ Successfully connected to Wi-Fi Direct!")
        printer_ip = discover_printer_ip()
        if printer_ip:
            print(f"🖨 Printer IP: {printer_ip}")
        else:
            print("⚠ Could not discover printer IP, but Wi-Fi Direct is connected.")

    if bluetooth_mac:
        print(f"🔄 Connecting to Bluetooth device: {bluetooth_mac}")
        bluetooth_response = connect_to_bluetooth(bluetooth_mac)
        print(bluetooth_response)
