from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from urllib.parse import urlparse, parse_qs
from datetime import datetime

import time
import helpers

# custom modules
from settings import MindBodyCredentials, BookingsWebsite


def get_avail_bookings(url):
    """Return a list of all the available bookings from the `url`"""

    options = Options()
    # options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)
    # driver = webdriver.Firefox()

    driver.get(url)

    # wait for a button to appear
    try:
        wait = WebDriverWait(driver, 30)
        wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//button[@class='bw-widget__signup-now bw-widget__cta']")
            )
        )
    except TimeoutException:
        return
    # wait a bit more
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
        dt = helpers.extract_datetime(qs["item[info]"][0])
        # print(f"{dt} [{btn.text}]")
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
            print(f"Found [{appt['text']}] for {appt['datetime']}")
            send_booking_request(appt["url"])


def send_booking_request(url):
    """Make the booking for the given booking `url`"""

    user = MindBodyCredentials.USER
    pwd = MindBodyCredentials.PWD

    options = Options()
    # options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)
    # driver = webdriver.Firefox()

    driver.get(url)

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

    # wait for green tick
    try:
        wait = WebDriverWait(driver, 10)
        element = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class='thank thank-booking-complete']")
            )
        )
        print("Booked!")
    except:
        print("couldnt book")

    # close the browser
    driver.close()


if __name__ == "__main__":
    # while True:
    #     if datetime.now().hour in [5, 9]:
    #         if datetime.now().minute in list(range(15)):
    #             print("\n===", datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), "===")
    #             get_avail_bookings()
    #     time.sleep(60)

    wishlist = [datetime(2024, 3, 21, 11, 30)]
    available = get_avail_bookings(BookingsWebsite.URL)
    book(available, wishlist)
