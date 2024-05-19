# app/services/sim800c_service.py
import re
import time
from enum import Enum

import serial

from app.dependencies import SERIAL_PORT, BAUD_RATE, OTP_TEMPLATE, OTP_TIMEOUT
from app.services.logger import setup_logger

# Configure logger
logger = setup_logger(__name__)


class SmsModem:
    def __init__(self):
        try:
            logger.debug("Initializing the SMS modem.")
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            self.initialize_modem()
        except serial.SerialException as e:
            logger.error(f"Failed to initialize modem: {e}")
            raise

    def initialize_modem(self):
        try:
            logger.debug("Setting up the modem configurations.")
            self.writeline('ATE0')  # Turn off command echo
            self.writeline('AT+CMGF=1')  # Set SMS to text mode
            self.writeline('AT+CPMS="SM","SM","SM"')  # Preferred SMS storage
            self.writeline('AT+CMGDA="DEL ALL"')  # Delete all SMS
            logger.info("Modem initialized and configured.")
        except Exception as e:
            logger.error(f"Failed to configure modem: {e}")
            raise

    def writeline(self, text):
        try:
            logger.debug(f"Sending command to modem: {text}")
            self.ser.write((text + '\r').encode())
        except serial.SerialTimeoutException as e:
            logger.error(f"Timeout during sending command to modem: {text}, Error: {e}")
            raise

    def receive(self):
        start_time = time.time()
        while True:
            if time.time() - start_time > OTP_TIMEOUT:
                logger.warning("Timeout reached while waiting for SMS.")
                return None
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line:
                    logger.debug(f"Received line from modem: {line}")
                    return line
            except serial.SerialException as e:
                logger.error(f"Error during receiving data from modem: {e}")
                raise
            except Exception as e:
                logger.error(f"Unhandled exception during receiving data from modem: {e}")
                raise
            time.sleep(1)


class Indication(Enum):
    UNKNOWN = 0
    RX_SMS = 1
    TEXT = 2
    OK = 4
    ERROR = 5
    POWEROFF = 6


def message_type(message):
    logger.debug(f"Evaluating message type: {message}")
    if message:
        if "+CMTI" in message:
            index = re.search(r'\d+', message).group()
            logger.info(f"New SMS received: {index}")
            return Indication.RX_SMS, index
        if "OK" in message:
            return Indication.OK, None
        if "ERROR" in message:
            logger.error("Received an error response from modem.")
            return Indication.ERROR, None
    return Indication.UNKNOWN, message


def process_sms(modem, index):
    logger.info(f"Processing SMS at index: {index}")
    modem.writeline(f"AT+CMGR={index}")
    sms_content = ""
    while True:
        line = modem.receive()
        if "+CMGR:" in line:
            continue
        elif "OK" in line:
            break
        elif line:
            sms_content += line + "\n"
    logger.info(f"SMS content received: {sms_content.strip()}")
    return sms_content.strip()


def extract_otp(sms_content):
    logger.debug("Extracting OTP from SMS content.")
    match = re.search(OTP_TEMPLATE, sms_content)
    if match:
        otp = match.group(1)
        logger.info(f"OTP extracted: {otp}")
        return otp
    logger.warning("No OTP found in the SMS content.")
    return None
