import subprocess
import socket
import time
from bleak import BleakClient
import bluetooth
from zeroconf import Zeroconf, ServiceBrowser

def connect_to_wifi_direct(ssid, auth_type, password):
    try:
        if auth_type.lower() == "open":
            wpa_supplicant_conf = f"""
network={{
    ssid="{ssid}"
    key_mgmt=NONE
}}
"""
        else:
            wpa_supplicant_conf = f"""
network={{
    ssid="{ssid}"
    key_mgmt=WPA-PSK
    psk="{password}"
}}
"""

        config_path = "/wpa_supplicant/wpa_supplicant-wifi-direct.conf"

        with open(config_path, "w") as config_file:
            config_file.write(wpa_supplicant_conf.strip())

        subprocess.run(["wpa_supplicant", "-B", "-i", "wlan0", "-c", config_path], check=True)
        subprocess.run(["dhclient", "wlan0"], check=True)

        printer_ip = discover_printer_ip()
        if not printer_ip:
            raise Exception("Failed to discover printer IP address.")

        return {"status": "success", "printer_ip": printer_ip}

    except subprocess.CalledProcessError as e:
        return {"status": "failed", "error": str(e)}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

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
    except Exception:
        return None

async def connect_to_bluetooth(bluetooth_mac):
    try:
        async with BleakClient(bluetooth_mac) as client:
            is_connected = await client.is_connected()
            if is_connected:
                return {"status": "success", "message": f"Connected to Bluetooth device {bluetooth_mac}."}
            else:
                return {"status": "failed", "error": f"Failed to connect to Bluetooth device {bluetooth_mac}."}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def find_bluetooth_mac_by_name(bluetooth_name):
    try:
        nearby_devices = bluetooth.discover_devices(lookup_names=True, duration=8)
        for mac_address, name in nearby_devices:
            if bluetooth_name.lower() in name.lower():
                return mac_address
        raise Exception(f"Bluetooth device with name '{bluetooth_name}' not found.")
    except bluetooth.BluetoothError:
        return None
    except Exception:
        return None
