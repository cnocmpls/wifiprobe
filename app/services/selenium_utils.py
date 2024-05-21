# app/services/selenium_utils.py
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from app.services.sim800c_service import SmsModem, extract_otp, process_sms, message_type, Indication, receive_otp

from app.dependencies import captive_portal_url, url_to_check
from app.services.logger import setup_logger

# Configure logger
logger = setup_logger(__name__)


def get_driver():
    logger.debug("Initializing the web driver.")
    options = Options()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--headless")
    service = Service('/usr/bin/chromedriver')
    # service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
#    driver.get(captive_portal_url)
#    logger.info("Browser opened and navigated to the captive portal URL.")
    return driver

def check_for_captive_portal(driver):
    """
    Checks if there is a captive portal by trying to navigate to a common website and checking for redirects.
    """
    try:
        driver.get(url_to_check)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "html")))
        current_url = driver.current_url
        logger.debug(f'Current URL: {current_url}')
        if "login" in current_url or "captive" in current_url or "portal" in current_url or captive_portal_url.split('https://')[1] in current_url:
            logger.info(f"Detected a captive portal at {current_url}")
            return True, current_url
        return False, None
    except Exception as e:
        logger.error("Error checking for captive portal", exc_info=True)
        return False, None


def navigate_to_captive_portal(driver):
    try:
        captive_flag, captive_url = check_for_captive_portal(driver)
        if captive_flag:
            driver.get(captive_url)
            logger.info("Browser opened and navigated to the captured captive portal URL.")
            return True, captive_url
        else:
            driver.get(captive_portal_url)
            logger.info("Browser opened and navigated to the manual captive portal URL.")
            return False, captive_portal_url
    except Exception as e:
        logger.error("Error opening captive portal", exc_info=True)
        return False, captive_portal_url


def enter_mobile_number(driver, mobile_number):
    logger.debug("Attempting to enter mobile number and request OTP.")
    """Enter the mobile number and request OTP."""
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Connect To Wi-Fi')]")))
    time.sleep(10)  # Ensure the 10 seconds have passed since page load
    # Click the button
    button = driver.find_element(By.XPATH, "//span[contains(text(), 'Connect To Wi-Fi')]")
    button.click()
    logger.info("Clicked on 'Connect To Wi-Fi' button.")

    # Enter the mobile number
    phone_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'phoneNumber'))
    )
    phone_input.send_keys(mobile_number)
    logger.info(f"Mobile number {mobile_number} entered.")

    # Click on the 'Send Code' button
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//button[contains(@class, "enter-btn")]'))
    ).click()
    logger.info("Mobile number submitted for verification.")



#def skip_ad(driver):
#    logger.debug("Attempting to skip ad to get internet access.")
#    try:
#        button_xpath = "//button[contains(text(), 'Skip Ad to Connect WiFi')]"
#        WebDriverWait(driver, 20).until(
#            EC.element_to_be_clickable((By.XPATH, button_xpath)),
#            message="Skip Ad button is not clickable."
#        )
#        skip_ad_button = driver.find_element(By.XPATH, button_xpath)
#        if skip_ad_button:
#            logger.info("Skip Ad button is visible.")
#        else:
#            logger.info("Skip Ad button is not visible")

#        skip_ad_button.click()
#        logger.info("Clicked on 'Skip Ad to Connect WiFi' button successfully.")
#        return True
#    except TimeoutException as e:
#        logger.error(f"Could not find or click on Skip Ad button: {e}")
#        return False
#    except NoSuchElementException as e:
#        logger.error(f"Skip Ad button not found: {e}")
#        return False
#    except Exception as e:
#        logger.error(f"An error occurred while trying to skip ad: {e}")
#        return False

def skip_ad(driver):
    logger.debug("Attempting to skip ad to get internet access.")
    try:
        button_xpath = "//button[contains(text(), 'Skip Ad to Connect WiFi')]"
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, button_xpath)),
            message="Skip Ad button is not clickable."
        )
        skip_ad_button = driver.find_element(By.XPATH, button_xpath)
        if skip_ad_button:
            logger.info("Skip Ad button is visible.")
        else:
            logger.info("Skip Ad button is not visible")

        skip_ad_button.click()
        logger.info("Clicked on 'Skip Ad to Connect WiFi' button successfully.")

        # Check for alert after clicking the Skip Ad button
        try:
            WebDriverWait(driver, 5).until(EC.alert_is_present(),
                                           "Waiting for alert after clicking 'Skip Ad'.")
            alert = driver.switch_to.alert
            alert_text = alert.text
            logger.info(f"Alert detected: {alert_text}")
            if "Free plan limit exhausted for the day" in alert_text:
                logger.warning("Free plan limit exhausted for the day.")
                alert.accept()  # Close the alert
                return False
            else:
                alert.accept()  # Close any other alerts
        except TimeoutException:
            logger.info("No alert detected after clicking 'Skip Ad'.")
        except NoAlertPresentException:
            logger.info("No alert present to handle.")

        return True
    except TimeoutException as e:
        logger.error(f"Could not find or click on Skip Ad button: {e}")
        return False
    except NoSuchElementException as e:
        logger.error(f"Skip Ad button not found: {e}")
        return False
    except Exception as e:
        logger.error(f"An error occurred while trying to skip ad: {e}")
        return False


def submit_otp(driver, otp):
    logger.debug("Attempting to submit OTP.")
    """Submit the OTP to complete the login process."""
    # Wait for the OTP input field to be clickable and enter the OTP
    otp_input = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input.form-control[type='number'][placeholder='Enter OTP']"))
    )
    otp_input.clear()  # Clear any pre-filled text
    otp_input.send_keys(otp)
    logger.info(f"OTP {otp} entered.")

    # Wait for the Verify button to be clickable and click it
    verify_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.verify-btn.btn.btn-primary"))
    )
    verify_button.click()
    logger.info("OTP submitted for verification.")


def check_internet_connection(driver, url_to_check="http://example.com"):
    logger.debug("Checking internet connection status.")
    try:
        driver.get(url_to_check)
        # Wait for the HTML content to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "html")))
        # Check for the specific h1 tag and its text
        heading = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h1[text()='Example Domain']")))
        if heading:
            logger.info("Internet connection established with Example Domain.")
            return True
        else:
            logger.warning("Example Domain heading not found.")
            return False
    except Exception as e:
        logger.error(f"Failed to navigate to {url_to_check}: {str(e)}")
        return False


def check_wifi_connection_success(driver):
    try:
        logger.debug("Checking for the 'connected to WiFi' message.")
        # Wait for the message indicating connection
        success_message = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.wifi-connect")),
            message="Did not find the success message for WiFi connection."
        )
        # Check the text of the success message
        if "Congratulations!!! You are connected to RailWire WIFI" in success_message.text:
            logger.info("Success message detected: User is connected to WiFi.")
            return True
        else:
            logger.warning("The message text does not confirm WiFi connection.")
            return False
    except TimeoutException:
        logger.error("Timeout while waiting for the WiFi connection message.")
        return False
    except NoSuchElementException:
        logger.error("The element containing the WiFi connection message does not exist.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False


def determine_next_step(driver):
    logger.debug("Determining the next step after entering the mobile number.")
    try:
        try:
            logger.info("Checking for OTP input presence.")
            # Check if the OTP input field is present
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='number'][placeholder='Enter OTP']"))
            )
            logger.info("OTP input field is visible.")
            return 'otp'
        except TimeoutException:
            try:
                logger.debug("OTP input not found.")
                # Check for the "Skip Ad" button if OTP input is not present
                logger.info("Checking for Skip Ad button presence.")
                button_xpath = "//button[contains(text(), 'Skip Ad to Connect WiFi')]"
                WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.XPATH, button_xpath)),
                    message="Skip Ad button is not visible."
                )
                skip_ad_button = driver.find_element(By.XPATH, button_xpath)
                if skip_ad_button:
                    logger.info("Skip Ad button is visible.")
                else:
                    logger.info("Skip Ad button is not visible")
                    return 'error'
                return 'skip_ad'
            except TimeoutException:
                logger.error("Neither OTP input nor Skip Ad button was found.", exc_info=True)
                return "Neither OTP input nor Skip Ad button was found."
    except Exception as e:
        logger.error("Error determining the next step: " + str(e), exc_info=True)
        return 'error'

def handle_portal_interaction(driver, mobile_number,sms_modem):
    enter_mobile_number(driver, mobile_number)
    next_step = determine_next_step(driver)
    if next_step == 'otp':
        otp = receive_otp(sms_modem)
        if otp:
            submit_otp(driver, otp)
            ad = skip_ad(driver)
            if ad:
                check_wifi_connection_success(driver)
                connected = check_internet_connection(driver)
                return {"Internet Connection": connected}
    elif next_step == 'skip_ad':
        ad = skip_ad(driver)
        if ad:
            check_wifi_connection_success(driver)
            connected = check_internet_connection(driver)
            return {"Internet Connection": connected}
        # Assuming clicking the 'Skip Ad' button navigates to a confirmation screen or the internet
    else:
        raise Exception("Failed to determine next step at the captive portal.")
