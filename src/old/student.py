import json
import time
import signal
import traceback
import threading
from selenium import webdriver
from contextlib import contextmanager
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException

terminate = threading.Event()
with open('credentials.json') as creds:
    credentials = json.load(creds)

@contextmanager
def get_driver():
    option = webdriver.ChromeOptions()
    chrome_prefs = {}
    option.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
    option.add_argument('user-data-dir=/home/druid/.config/google-chrome/droidprofile')  # noqa: E501
    option.add_extension('uBlock-Origin.crx')
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
    while not terminate.is_set():
        try:
            return WebDriverWait(driver, 20).until(EC.visibility_of_element_located(locate)) # noqa: E501
        except Exception as e:
            print(e, type(e))

@contextmanager
def login(driver):
    global terminate
    try:
        elearning = "https://ielearning.ueab.ac.ke"
        auth = (credentials['username'], credentials['password'])
        driver.get(elearning)
        try:
            text = driver.find_element(By.CLASS_NAME, 'logininfo').text
            if 'You are not logged in' not in text:
                yield text
                return
        except Exception:
            pass
        while not terminate.is_set():
            try:
                wait(driver, (By.CLASS_NAME, 'usermenu')).click()
                break
            except ElementClickInterceptedException:
                time.sleep(2)
                continue
        driver.find_element(By.ID, 'username').send_keys(auth[0])
        driver.find_element(By.ID, 'password').send_keys(auth[1])
        driver.find_element(By.ID, 'loginbtn').click()
        yield wait(driver, (By.CLASS_NAME, 'logininfo')).text.split('(')[0].strip()
    except Exception as e:
        print(e)
        yield
    return

def main():
    global terminate
    signal.signal(signal.SIGINT, stop)
    with get_driver() as driver:
        with login(driver) as logged_in:
            if not logged_in:
                raise RuntimeError('Login failed.')
            print(logged_in)
            driver.get('https://ielearning.ueab.ac.ke/my/')
            ls = wait(driver, (By.CLASS_NAME, 'list-group'))
            print(ls)
            out = ''.join([i.text for i in driver.find_elements(By.CLASS_NAME, 'list-group')]) # noqa: E501
            print(out)
            breakpoint()
            terminate.wait()


if __name__ == '__main__':
    main()
