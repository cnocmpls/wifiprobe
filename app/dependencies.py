import logging
import os

url_to_check = os.environ.get("TESTING_URL","http://example.com")
captive_portal_url = os.environ.get("CAPTIVE_PORTAL_URL", "https://cpts.piponet.in")
SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/serial0")
BAUD_RATE = os.environ.get("BAUD_RATE", "115200")
OTP_TEMPLATE = os.environ.get("OTP_TEMPLATE", "Railwire WiFi OTP sponsored by BPCL is (\\d+)")
OTP_TIMEOUT = int(os.environ.get("OTP_TIMEOUT", "60"))

DEFAULT_LOG_LEVEL = "DEBUG"
LOG_LEVEL = os.getenv("LOGGING_LEVEL", DEFAULT_LOG_LEVEL).upper()
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", DEFAULT_LOG_LEVEL).upper()

LOG_LEVEL_MAPPING = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
