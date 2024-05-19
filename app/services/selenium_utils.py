# app/services/selenium_utils.py
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.dependencies import captive_portal_url
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
    driver.get(captive_portal_url)
    logger.info("Browser opened and navigated to the captive portal URL.")
    return driver


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
    logger.info("OTP request sent.")


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


def check_internet_connection(driver):
    logger.debug("Checking internet connection status.")
    """Check if the internet connection has been established."""
    driver.get('http://example.com')
    if "Example Domain" in driver.title:
        logger.info("Internet connection established!")
        return True
    else:
        logger.warning("Failed to establish an internet connection.")
        return False
