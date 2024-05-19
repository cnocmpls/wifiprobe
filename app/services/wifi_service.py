# app/services/wifi_service.py
import time
from typing import List

from pywifi import PyWiFi, const

from app.schemas.network import Network
from app.services.logger import setup_logger

# Configure logger
logger = setup_logger(__name__)


# def get_wifi_interfaces() -> List[NetworkInterface]:
#     try:
#         wifi = PyWiFi()
#         if not wifi.interfaces():
#             logger.error("No Wi-Fi interfaces found.")
#             raise ValueError("No Wi-Fi interfaces available")
#
#         interfaces = wifi.interfaces()
#         logger.info(f"Found {len(interfaces)} Wi-Fi interfaces.")
#         logger.debug(f"Interfaces: {interfaces}")
#
#         interfaces = wifi.interfaces()
#
#         network_interfaces = []
#         for iface in interfaces:
#
#                 network_interfaces.append(NetworkInterface(
#                     name=iface.name(),
#                     description=f"Interface GUID: {guid}",
#                     mac_address=mac_address,
#                     ip_address=ip_address,
#                     index=iface.index(),
#                     status='Unknown'  # Placeholder for status, replace as needed
#                 ))
#         return network_interfaces
#     except Exception as e:
#         logger.error("Failed to fetch Wi-Fi interfaces", exc_info=True)
#         raise e
#
# # def get_wifi_interfaces() -> List[NetworkInterface]:
# #     try:
# #         wifi = PyWiFi()
# #         if not wifi.interfaces():
# #             logger.error("No Wi-Fi interfaces found.")
# #             raise ValueError("No Wi-Fi interfaces available")
# #
# #         interfaces = wifi.interfaces()
# #         logger.info(f"Found {len(interfaces)} Wi-Fi interfaces.")
# #         return [NetworkInterface(index=i, name=iface.name(), description=iface.name()) for i, iface in enumerate(interfaces)]
# #     except Exception as e:
# #         logger.error("Failed to fetch Wi-Fi interfaces", exc_info=True)
# #         raise e
#
# def get_wifi_interfaces() -> List[NetworkInterface]:
#     try:
#         wifi = PyWiFi()
#
#         netiface_interfaces = netifaces.interfaces()
#         print(netiface_interfaces)
#         if not netiface_interfaces:
#             logger.error("No network interfaces found.")
#             raise ValueError("No network interfaces available")
#
#
#         interfaces = wifi.interfaces()
#         if not interfaces:
#             logger.error("No Wi-Fi interfaces found.")
#             raise ValueError("No Wi-Fi interfaces available")
#
#         for interface in interfaces:
#             print('Pywifi interface:', interface, interface.name(), interface.status())
#             # print(interface.name(), interface.status())
#         for iface in netiface_interfaces:
#             print('Netifaces interface:', iface, netifaces.ifaddresses(iface), netifaces.AF_LINK, netifaces.ifaddresses(iface).get(netifaces.AF_LINK, [{}])[0].get('addr', 'Unknown'))
#             # print(iface, netifaces.ifaddresses(iface), netifaces.AF_LINK, netifaces.ifaddresses(iface).get(netifaces.AF_LINK, [{}])[0].get('addr', 'Unknown'))
#
#
#         logger.info(f"Found {len(interfaces)} Wi-Fi interfaces.")
#         network_interfaces = []
#         for index, iface in enumerate(interfaces):
#             status = iface.status()
#             status_description = {
#                 const.IFACE_DISCONNECTED: "Disconnected",
#                 const.IFACE_SCANNING: "Scanning",
#                 const.IFACE_INACTIVE: "Inactive",
#                 const.IFACE_CONNECTING: "Connecting",
#                 const.IFACE_CONNECTED: "Connected",
#             }.get(status, "Unknown")
#
#
#             mac_address = netifaces.ifaddresses(iface.name()).get(netifaces.AF_LINK, [{}])[0].get('addr', 'Unknown')
#
#             iface_info = NetworkInterface(
#                 index=index,
#                 name=iface.name(),
#                 description=iface.name(),
#                 mac_address=mac_address,
#                 status=status_description
#             )
#             network_interfaces.append(iface_info)
#         return network_interfaces
#     except Exception as e:
#         logger.error("Failed to fetch Wi-Fi interfaces", exc_info=True)
#         raise e

def scan_wifi_networks(interface_index: int = 0) -> List[Network]:
    wifi = PyWiFi()
    if interface_index >= len(wifi.interfaces()):
        logger.error("Interface index out of range")
        return []

    iface = wifi.interfaces()[interface_index]
    iface.scan()
    time.sleep(5)  # Sleep to allow for scan to complete
    results = iface.scan_results()

    networks = []
    for net in results:
        try:
            network_data = {
                "ssid": net.ssid,
                "bssid": net.bssid,
                "signal": net.signal,
                "frequency": getattr(net, 'freq', None),  # Use None as a default if frequency is not available
                "security": convert_security_type(net.akm[-1] if net.akm else const.AKM_TYPE_NONE),
                "auth_algorithm": convert_auth_algorithm(net.auth if hasattr(net, 'auth') else [const.AUTH_ALG_OPEN]),
                "network_type": "Infrastructure"  # Assuming all scanned networks are infrastructure type
            }
            networks.append(Network(**network_data))
        except Exception as e:
            logger.error(f"Error processing network data: {e}", exc_info=True)

    logger.info(f"Scan completed on interface {iface.name()}. Found {len(networks)} networks.")
    return networks


def convert_auth_algorithm(auth_alg):
    # Convert the list to a tuple to make it hashable if it's not already a string or tuple
    if isinstance(auth_alg, list):
        auth_alg = tuple(auth_alg)

    auth_algorithm_mapping = {
        (const.AUTH_ALG_OPEN,): 'Open',
        (const.AUTH_ALG_SHARED,): 'Shared',
    }
    return auth_algorithm_mapping.get(auth_alg, "Unknown")


def convert_security_type(akm_type):
    return {
        const.AKM_TYPE_NONE: 'None',
        const.AKM_TYPE_WPA: 'WPA',
        const.AKM_TYPE_WPAPSK: 'WPA-PSK',
        const.AKM_TYPE_WPA2: 'WPA2',
        const.AKM_TYPE_WPA2PSK: 'WPA2-PSK'
    }.get(akm_type, 'Unknown')
