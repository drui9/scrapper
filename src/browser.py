import json
import time
import signal
import traceback
import threading
from selenium import webdriver
from contextlib import contextmanager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException


@contextmanager
def get_driver():
    option = webdriver.ChromeOptions()
    chrome_prefs = {}
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
    option.experimental_options["prefs"] = chrome_prefs
    option.add_argument('--disable-setuid-sandbox')
    option.add_argument('disable-infobars')
    option.add_argument('start-maximized')
    option.add_argument('--disable-dev-shm-using')
    option.add_extension('resources/uBlock-Origin.crx')
    option.add_extension('resources/istilldontcareaboutcookies-1.1.1.crx')
    driver = webdriver.Chrome(options=option)
    try:
        yield driver
    finally:
        driver.close()

def stop(*args):
    global terminate
    terminate.set()
    return

def wait(driver, locate):
    global terminate
    while not terminate.is_set():
        try:
            return WebDriverWait(driver, 20).until(EC.visibility_of_element_located(locate)) # noqa: E501
        except Exception as e:
            print(type(e))

def main():
    global terminate
    signal.signal(signal.SIGINT, stop)
    with get_driver() as driver:
        driver.get('https://google.com')
        breakpoint()

if __name__ == '__main__':
    terminate = threading.Event()
    main()
