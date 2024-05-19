# app/services/network_service.py

import socket

import psutil
from pydantic import ValidationError
from pywifi import PyWiFi, const

from app.schemas.network_interface import AllNetworkInterfaces
from app.services.logger import setup_logger

# Configure logger
logger = setup_logger(__name__)


def fetch_network_details() -> AllNetworkInterfaces:
    interfaces_details = {}
    all_if_addrs = psutil.net_if_addrs()
    all_if_stats = psutil.net_if_stats()
    wifi = PyWiFi()
    if not wifi.interfaces():
        logger.error("No Wi-Fi interfaces found.")
        raise ValueError("No Wi-Fi interfaces available")
    all_wifi_interfaces = wifi.interfaces()
    logger.info(f"Found {len(all_if_addrs)} network interfaces.")
    for if_name, addrs in all_if_addrs.items():
        if_stats = all_if_stats.get(if_name, None)
        for index,wifiiface in enumerate(all_wifi_interfaces):
            if wifiiface.name() == if_name:
                is_wifi = True
                status = wifiiface.status()
                wifi_index = index
                status = {
                    const.IFACE_DISCONNECTED: "Disconnected",
                    const.IFACE_SCANNING: "Scanning",
                    const.IFACE_INACTIVE: "Inactive",
                    const.IFACE_CONNECTING: "Connecting",
                    const.IFACE_CONNECTED: "Connected",
                }.get(status, "Unknown")
            else:
                is_wifi = False
                status = "Unknown"
                wifi_index = 0


        interface_detail = {
            "mac_address": None,
            "ipv4": [],
            "ipv6": [],
            "is_up": if_stats.isup if if_stats else False,
            "speed": if_stats.speed if if_stats else 0,
            "duplex": if_stats.duplex.name if if_stats else "Unknown",
            "mtu": if_stats.mtu if if_stats else 0,
            "is_wifi": is_wifi if is_wifi else False,
            "index": wifi_index if wifi_index else 0,
            "status": status if status else "Unknown",
            "name": if_name,
        }
        for addr in addrs:
            ip_detail = {"address": addr.address, "netmask": addr.netmask, "broadcast": addr.broadcast}
            if addr.family == socket.AF_INET:
                interface_detail["ipv4"].append(ip_detail)
            elif addr.family == socket.AF_INET6:
                interface_detail["ipv6"].append(ip_detail)
            elif addr.family == psutil.AF_LINK:
                interface_detail["mac_address"] = addr.address

        interfaces_details[if_name] = interface_detail
        logger.debug(f"Interface details: {interfaces_details}")
    try:
        return AllNetworkInterfaces(interfaces=interfaces_details)
    except ValidationError as e:
        print("Error validating network data:", e)
        return None

def fetch_wifi_interfaces() -> AllNetworkInterfaces:
    logger.info("Fetching Wi-Fi interfaces.")
    logger.debug("Fetching all network interfaces.")
    interfaces = fetch_network_details()
    logger.debug(f"Found {len(interfaces.interfaces)} network interfaces.")
    logger.debug("Filtering Wi-Fi interfaces.")
    wifi_interfaces = AllNetworkInterfaces(interfaces={interface: interfaces.interfaces[interface] for interface in interfaces.interfaces if interfaces.interfaces[interface].is_wifi})

    logger.debug(f"Found {len(wifi_interfaces.interfaces)} Wi-Fi interfaces.")
    return wifi_interfaces
