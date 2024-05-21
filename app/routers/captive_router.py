# app/routers/captive_router.py
from fastapi import APIRouter, HTTPException, Depends
from selenium.webdriver.chrome.webdriver import WebDriver

from app.schemas.captive_portal import MobileNumber
from app.schemas.wifi import WiFiTest
from app.services.logger import setup_logger
from app.services.selenium_utils import enter_mobile_number, submit_otp, check_internet_connection, get_driver, navigate_to_captive_portal, skip_ad, handle_portal_interaction
from app.services.sim800c_service import SmsModem, extract_otp, process_sms, message_type, Indication, receive_otp
from app.services.wifi_service import scan_wifi_networks, connect_to_network

# Configure logger
logger = setup_logger(__name__)

router = APIRouter()


# Dependency to get the SMS Modem instance
def get_sms_modem():
    return SmsModem()

@router.post("/check-internet-connection/")
async def initiate_test(driver: WebDriver = Depends(get_driver)):
    logger.info("Trying to check if internet connection is there.")
    try:
        connected = check_internet_connection(driver)
        return {"Internet Connection": connected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/initiate-manual-test/")
async def initiate_test(data: MobileNumber, driver: WebDriver = Depends(get_driver),
                        sms_modem: SmsModem = Depends(get_sms_modem)):
    logger.info("Requesting OTP for the mobile number.")
    try:
        # Step 1: Feed mobile number to the captive portal
        enter_mobile_number(driver, data.mobile_number)
        logger.info("OTP request process completed successfully.")

        # Step 2: Wait and receive OTP from SIM800C
        otp = None
        while otp is None:
            line = sms_modem.receive()
            indication, info = message_type(line)
            if indication == Indication.RX_SMS:
                #            if indication == message_type.Indication.RX_SMS:
                sms_content = process_sms(sms_modem, info)
                logger.debug(f"Recieved SMS content: {sms_content}.")
                otp = extract_otp(sms_content)

        # Step 3: Feed the OTP to the captive portal
        if otp:
            submit_otp(driver, otp)

        # Step 4: Check if the internet connection is established
        connected = check_internet_connection(driver)
        return {"Internet Connection": connected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-wifi/")
async def initiate_wifi_test(data: WiFiTest, driver: WebDriver = Depends(get_driver),
                        sms_modem: SmsModem = Depends(get_sms_modem)):
    logger.debug("Received request to automatically connect to Wi-Fi.")
    try:
        # Step 1: Scan for available networks and find the desired SSID
        ssid = data.ssid
        logger.debug("Scanning wifi networks")
        networks = scan_wifi_networks(data.interface_index)
        if not any(net.ssid == ssid for net in networks):
            logger.error(f"SSID '{ssid}' not found.")
            raise HTTPException(status_code=404, detail=f"SSID '{ssid}' not found.")
        logger.debug(f"SSID '{ssid}' found.")
        # Step 2: Connect to the network
        logger.debug(f"Trying to connect to SSID '{ssid}'.")
        connection_result = connect_to_network(data.interface_index,data.ssid, data.password)
        if not connection_result.get("connected"):
            logger.error(f"Failed to connect to SSID '{ssid}'.")
            raise HTTPException(status_code=400, detail="Failed to connect to the network.")
        logger.debug(f"Successfully connected to SSID '{ssid}'.")
        # Step 3: Check for a captive portal
        portal_exists, redirect_url = navigate_to_captive_portal(driver)
        if portal_exists:
            result = handle_portal_interaction(driver, data.mobile_number, sms_modem)
            if result:
                return {"message": "Internet access granted"}
            else:
                raise HTTPException(status_code=400, detail="Failed to gain internet access")

    except Exception as e:
        logger.error("An error occurred: " + str(e))
        raise HTTPException(status_code=500, detail=str(e))
