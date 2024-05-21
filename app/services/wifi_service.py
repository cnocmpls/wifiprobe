# app/services/wifi_service.py
import time
from typing import List

from pywifi import PyWiFi, const, Profile
from fastapi import HTTPException

from app.schemas.network import Network
from app.services.logger import setup_logger

# Configure logger
logger = setup_logger(__name__)


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


def get_best_wifi_interface():
    wifi = PyWiFi()
    if not wifi.interfaces():
        logger.error("No Wi-Fi interfaces found.")
        raise HTTPException(status_code=404, detail="No Wi-Fi interfaces available.")
    
    # Example criteria: choose the first available interface that is not connected
    for iface in wifi.interfaces():
        if iface.status() == const.IFACE_DISCONNECTED:
            logger.info(f"Selected interface {iface.name()} as the best available option.")
            return iface
    
    logger.warning("No suitable Wi-Fi interface found, selecting default.")
    return wifi.interfaces()[0]  # default to the first interface if none are disconnected


def connect_to_network(interface_index: int, ssid: str, password: str = None):
    wifi = PyWiFi()
    if interface_index >= len(wifi.interfaces()):
        logger.error("Interface index out of range")
        raise HTTPException(status_code=404, detail="Interface index out of range.")

    iface = wifi.interfaces()[interface_index]
    iface.disconnect()
    time.sleep(1)  # ensure the interface is disconnected

    profile = Profile()
    profile.ssid = ssid

    # Setting default for open network
    profile.auth = const.AUTH_ALG_OPEN
    profile.akm.append(const.AKM_TYPE_NONE)
    profile.cipher = const.CIPHER_TYPE_NONE

    if password:
        # Configure for WPA2PSK if password is provided
        profile.akm = [const.AKM_TYPE_WPA2PSK]
        profile.cipher = const.CIPHER_TYPE_CCMP
        profile.key = password
    elif password is None and not any(x == const.AKM_TYPE_NONE for x in profile.akm):
        logger.error("Password required for secured network")
        raise HTTPException(status_code=400, detail="Password required for secured network")

    iface.remove_all_network_profiles()
    tmp_profile = iface.add_network_profile(profile)

    logger.debug("Attempting to connect to network")
    iface.connect(tmp_profile)
    time.sleep(10)  # wait for connection to establish

    if iface.status() == const.IFACE_CONNECTED:
        logger.info("Connected to the network successfully")
        return {"connected": True, "status": "Connected to the network successfully"}
    else:
        logger.warning("Failed to connect to the network")
        return {"connected": False, "status": "Failed to connect to the network"}
