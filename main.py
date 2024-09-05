from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import re
import time
import logging
import sys
import argparse

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# my modules
from settings import Credentials
import utils
from my_logger import configure_logger

# initialise logger
logger = logging.getLogger(__name__)
configure_logger(logger, log_file="pilates_booker.log")


RETRY_MINUTES = 10


def get_web_driver(headless=True):
    options = Options()

    if headless:
        options.add_argument("--headless")

    return webdriver.Firefox(options=options)


def sign_in(driver, url="https://cart.mindbodyonline.com/sites/112721/session/new"):

    # open page
    driver.get(url)

    # login with credentials
    try:
        logger.info("waiting for login screen")
        wait = WebDriverWait(driver, 30)

        # populate user and password fields
        user_field = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input#username"))
        )
        pwd_field = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input#password"))
        )
        logger.info("logging in")
        user_field.send_keys(Credentials.USER)
        pwd_field.send_keys(Credentials.PWD)
        
        # press submit button
        element = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
        )
        element.click()

        # wait until logged in
        wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.icon__user-initials"))
        )
        logger.info("logged in")
    except Exception as e:
        logger.error(f"{type(e).__name__} - {e}")

    return driver


def get_avail_bookings(driver, url):
    """
    Return a list of all the available bookings from the `url`

    Args:
        driver (obj): webdriver
        url (str): The url of the website listing the available bookings.
    """

    # open page
    driver.get(url)

    # wait for a button to appear
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "button.bw-widget__signup-now.bw-widget__cta")
            )
        )
    except Exception as e:
        logger.error(f"{type(e).__name__} - {e}")

    # wait a bit longer
    # time.sleep(1)

    # get all buttons
    buttons = driver.find_elements(
        By.CSS_SELECTOR, "button.bw-widget__signup-now.bw-widget__cta"
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

    logger.info(f"Available bookings: {[b.get('datetime') for b in bookings]}")

    return bookings


def book(driver, avail_bookings, wishlist):
    """
    Loops through `avail_bookings`. For the ones that are in the `wishlist`, send a booking request

    Args:
        avail_bookings (list): List of dictionaries representing the available timeslots/appointments that can be booked.
        wishlist (list): List of timeslots wanting to book

    Returns:
        bool: `True` if booking made, else `False`
    """
    bookings_made = 0

    for appt in avail_bookings:
        if appt["datetime"] in wishlist:
            logger.info(f"Found [{appt['text']}] for {appt['datetime']}")
            if send_booking_request(driver, appt):
                bookings_made += 1

    if bookings_made == 0:
        return False
    else:
        logger.info("checkpoint")
        return True


def send_booking_request(driver, appt):
    """
    Make the booking using the booking url in `appt`

    Args:
        driver (obj): 
        appt (dict): Contains details of the "appointment" to book.
            Keys are `url`, `datetime`, and `text`.

    Returns:
        bool: `True` if booking made, else `False`
    """
    booked = False

    # for debugging
    logger.info(f"appt object: {appt}")

    # Open page
    driver.get(appt["url"])

    # click next
    wait = WebDriverWait(driver, 30)
    element = wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "a[href='/sites/112721/cart/proceed_to_checkout']")
        )
    )
    element.click()

    # wait for green tick (hopefully)
    try:
        logger.info("waiting for green tick (hopefully)")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.thank.thank-booking-complete")
            )
        )
        booked = True
        logger.info("Booked! 🙂")
        utils.update_record(appt["datetime"], "booked")

    except Exception as e:
        # check if you already had the booking
        banner = driver.find_elements(By.CSS_SELECTOR, "div.c-banner__title")

        if banner:
            logger.warning(f"Message from site banner: {banner[0].text}")

            if "already in class" in banner[0].text.lower():
                utils.update_record(appt["datetime"], "booked")
                booked = True

            elif "registered for another session" in banner[0].text.lower():
                utils.update_record(appt["datetime"], "booked")
                booked = True

            elif ("already in waitlist" in banner[0].text.lower()):
                utils.update_record(appt["datetime"], "waitlisted")
                booked = True

        else:
            logger.error(f"{type(e).__name__} - {e}")

    finally:
        return booked


if __name__ == "__main__":

    if wishlist := utils.get_wishlist():
        driver = get_web_driver()

        time_start = datetime.now()
        booked = False
        logger.info(f"Wishlist: {wishlist}")

        sign_in(driver)

        while not booked:
            available = get_avail_bookings(driver, Credentials.URL)
            booked = book(driver, available, wishlist)

            # retry if booking not made
            if not booked:
                # check within retry minutes
                if time_start > datetime.now() - timedelta(minutes=RETRY_MINUTES):
                    logger.warning("No available bookings for desired timeslot...retrying")
                    time.sleep(1)
                else:
                    logger.warning(f"RETRY_MINUTES ({RETRY_MINUTES}) expired")
                    break
        
        driver.close()

    else:
        logger.info(f"Skipping run...No wishlist items within booking window")
