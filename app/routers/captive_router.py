# app/routers/captive_router.py
from fastapi import APIRouter, HTTPException, Depends
from selenium.webdriver.chrome.webdriver import WebDriver

from app.schemas.captive_portal import MobileNumber
from app.services.logger import setup_logger
from app.services.selenium_utils import enter_mobile_number, submit_otp, check_internet_connection, get_driver
from app.services.sim800c_service import SmsModem, extract_otp, process_sms, message_type, Indication

# Configure logger
logger = setup_logger(__name__)

router = APIRouter()


# Dependency to get the SMS Modem instance
def get_sms_modem():
    return SmsModem()


@router.post("/initiate-test/")
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
