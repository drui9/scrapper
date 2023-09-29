import os
import re
import time
import queue
import shlex
import signal
import random
import socket
import threading
from fabric import Connection
from selenium import webdriver
from contextlib import contextmanager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException

def do_wait(loc, driver):
    try:
        return WebDriverWait(driver, 10).until(EC.presence_of_element_located(loc))
    except Exception:
        return

def downloader(source, terminate):
    signal.signal(signal.SIGINT, close)
    with driver_session() as driver:
        while not terminate.is_set():
            try:
                yturl = source.get(timeout=7)
                driver.get("https://www.y2mate.com/en848")
            except queue.Empty: # no work
                try: # try moving files
                    songs = [i for i in os.listdir(os.getcwd()) if '.mp3' in i[-4:]]
                    for sname in songs:
                        nname = sname.split(' - ')[-1]
                        os.system(f'mv {shlex.quote(sname)} ~/Music/{shlex.quote(nname)}')  # noqa: E501
                        toast(f'{nname} downloaded.')
                except Exception as e:
                    print(e)
                continue
            except WebDriverException:
                continue
            txt = do_wait((By.ID, "txt-url"), driver)
            if not txt:
                source.put(yturl)
                continue
            for ch in yturl:
                txt.send_keys(ch)
                time.sleep(random.uniform(0.001, 0.01))
            txt.send_keys(Keys.RETURN)
            audio = do_wait((By.XPATH, "//a[@href='#audio']"), driver)
            if not audio:
                source.put(yturl)
                continue
            audio.click()
            found = False
            for btn in [btn for btn in driver.find_elements(By.CLASS_NAME, 'btn-success') if 'Download' in btn.text]:  # noqa: E501
                try:
                    btn.click()
                    found = True
                except ElementNotInteractableException:
                    continue
            if not found:
                source.put(yturl)
                continue
            dlbtn = do_wait((By.CLASS_NAME, "btn-file"), driver)
            if not dlbtn:
                source.put(yturl)
                continue
            dlbtn.click()

@contextmanager
def driver_session():
    options = Options()
    prefs = {
        "download.default_directory": os.getcwd(),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    }
    options.add_experimental_option('prefs', prefs)
    options.add_argument('user-data-dir=/home/druid/.config/google-chrome/droidprofile') # custom profile  # noqa: E501
    options.add_extension('uBlock-Origin.crx') # load add-blocker
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.close()

def close(*args):
    terminate.set()

def execute(cmd):
    try:
        c = Connection('android')
        c.run(cmd)
        c.close()
    except Exception as e:
        print(e)

def main():
    port = 3132
    ip = '0.0.0.0'
    # 
    def refresh_notice():
        note = 'Youtube mp3 downloader'
        btn1 = f'--button1 next --button1-action "echo \\$REPLY|nc -q1 {ip} 192.168.43.128"' # noqa: E501
        btn2 = f'--button2 close --button2-action "echo terminate|nc -q1 {ip} 192.168.43.128"' # noqa: E501
        notice = f"termux-notification --alert-once --id youtube -t YoutubeDL -c '{note}' {btn1} {btn2}"  # noqa: E501
        notify(notice)
    # -- mobile notification in thread
    def ytdl_notification(into):
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((ip, port))
            sock.listen()
            sock.settimeout(4)
        except Exception as e:
            terminate.set()
            print(e)
        while not terminate.is_set():
            try:
                refresh_notice()
                conn, _ = sock.accept()
                conn.settimeout(2)
                if not (data := conn.recv(1024)):
                    conn.close()
                    continue
                conn.close()
            except Exception:
                continue
            if data == 'close':
                terminate.set()
                toast('Terminated.')
                break
            data = data.decode('utf8').split('?')[0]
            if (link := re.search(r'https:\/\/[\w\.-]+\/[\w\.-]+', data)):
                toast(f'Downloading {shlex.quote(data)}')
                source.put(link.string)
            else:
                if data.strip() == 'terminate':
                    close()
                    break
                error('Invalid youtube link!')
                continue
        print('---terminated---')
    #
    th = threading.Thread(target=ytdl_notification, args=(source,))
    th.start()
    downloader(source, terminate)
    th.join()

if __name__ == '__main__':
    source = queue.Queue()
    terminate = threading.Event()
    notify = lambda x: execute(x)  # noqa: E731
    toast = lambda x: execute(f'termux-toast -c lime -b black {x}')  # noqa: E731, E501
    error = lambda x: execute(f'termux-vibrate; termux-toast -g top -c lime -b black {x}')  # noqa: E731, E501
    main()
