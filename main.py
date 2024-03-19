from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from urllib.parse import urlparse, parse_qs
from datetime import datetime

import time
import utils
import logging
import json


logger = logging.getLogger(__name__)

logging.basicConfig(
    filename="pilates_booker.log",
    format="%(asctime)s.%(msecs)03d %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

# custom modules
from settings import MindBodyCredentials, BookingsWebsite


def get_avail_bookings(url):
    """Return a list of all the available bookings from the `url`"""

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)

    driver.get(url)

    # wait for a button to appear
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//button[@class='bw-widget__signup-now bw-widget__cta']")
            )
        )
    except Exception as e:
        logger.error(f"Error occured ☹️: {type(e).__name__} - {e}")


    # wait a bit longer
    time.sleep(2)

    # get all buttons
    buttons = driver.find_elements(
        By.XPATH, "//button[@class='bw-widget__signup-now bw-widget__cta']"
    )

    # to store all the booking detailss
    bookings = []

    # get booking info for each button
    for btn in buttons:
        book_url = btn.get_attribute("data-url")
        parsed_url = urlparse(book_url)
        qs = parse_qs(parsed_url.query)
        dt = utils.convert_booking_date_str(qs["item[info]"][0])
        bookings.append({"url": book_url, "datetime": dt, "text": btn.text})

    # close the browser
    driver.close()

    return bookings


def book(avail_bookings, wishlist):
    """Loops through `avail_bookings`.
    For the ones that are in the `wishlist`, send a booking request
    """

    for appt in avail_bookings:
        if appt["datetime"] in wishlist:
            logger.info(f"Found [{appt['text']}] for {appt['datetime']}")
            send_booking_request(appt)


def send_booking_request(appt):
    """Make the booking for the given booking `url`"""

    user = MindBodyCredentials.USER
    pwd = MindBodyCredentials.PWD

    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)

    driver.get(appt["url"])

    # click next
    wait = WebDriverWait(driver, 10)
    element = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//a[@href='/sites/112721/cart/proceed_to_checkout']")
        )
    )
    element.click()

    # login
    try:
        user_field = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//input[@id='username']"))
        )
        pwd_field = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//input[@id='password']"))
        )

        time.sleep(1)
        user_field.send_keys(user)
        time.sleep(1)
        pwd_field.send_keys(pwd)
        time.sleep(1)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()

    except TimeoutException:
        # probably already logged in?
        pass

    # wait for green tick (hopefully)
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='thank thank-booking-complete']"))
        )
        logger.info("Booked! 🙂")
        utils.update_record(appt["datetime"], "booked")

    except TimeoutException:
        banner = driver.find_elements(By.XPATH, "//div[@class='c-banner__title']")
        if banner:
            logger.warning(f"Couldn't book ☹️: Message from site banner - {banner[0].text}")
            if "already in waitlist" in banner[0].text:
                utils.update_record(appt["datetime"], "booked")
        else:
            logger.warning(f"Coulldn't book ☹️: {type(e).__name__} - {e}")
            
    except Exception as e:
        logger.error(f"Error occured ☹️: {type(e).__name__} - {e}")

    # close the browser
    driver.close()


if __name__ == "__main__":

    if wishlist := utils.get_wishlist():
        logger.info(f"Wishlist: {wishlist}")

        available = get_avail_bookings(BookingsWebsite.URL)
        logger.info(f"Available bookings: {[a.get('datetime') for a in available]}")

        book(available, wishlist)
    else:
        logger.info(f"Skipping run...No wishlist items within booking window")
