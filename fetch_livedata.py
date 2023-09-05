from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import time
import os
from webdriver_manager.chrome import ChromeDriverManager

username = os.environ.get("selenium_username")
password = os.environ.get("selenium_password")

def fetch_livedata(email):
    storage_data = {}
    driver = None
    try:
        options = Options()
        options.add_argument('--incognito')
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')

        chrome_prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.javascript": 1,
            "profile.managed_default_content_settings.plugins": 1,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        options.experimental_options["prefs"] = chrome_prefs

        chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
        if not os.path.exists(chromedriver_path):
            chromedriver_path = ChromeDriverManager().install()

        service = ChromeService(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)

        driver.get("https://admin.google.com/")

        wait = WebDriverWait(driver, 25)

        # Google
        email_field = wait.until(EC.element_to_be_clickable((By.ID, "identifierId")))
        email_field.send_keys(username)
        email_field.send_keys(Keys.ENTER)

        # SSO
        username_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='Uniqname or Friend ID']")))
        username_field.click()
        username_field.send_keys(username)

        password_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Password']")
        password_field.click()
        password_field.send_keys(password)
        password_field.send_keys(Keys.ENTER)

        time.sleep(3)

        driver.get("https://admin.google.com/")

        search_box = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'input[aria-label="Search for users, groups or settings"]')))
        search_box.clear()
        search_box.send_keys(email)

        try:
            first_user_option = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.MkjOTb.oKubKe.nwSHjc[data-index="0"]'))
            )
            first_user_option.click()
        except StaleElementReferenceException:
            first_user_option = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.MkjOTb.oKubKe.nwSHjc[data-index="0"]'))
            )
            first_user_option.click()

        try:
            storage_amount_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.PZFh5b')))
            storage_amount = parse_storage_string(storage_amount_element.text)
        except TimeoutException:
            try:
                storage_amount_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.zhGlPe')))
                storage_amount = parse_storage_string(storage_amount_element.text)
            except TimeoutException as e:
                print(f"Neither span.PZFh5b nor div.zhGlPe were found: {e}")
                storage_amount = None

        if storage_amount is not None:
            storage_data[email] = storage_amount

    except Exception as e:
        print(f"Error occurred for user {email}: {e}")
    finally:
        if driver is not None:
            driver.quit()

    return storage_data

def parse_storage_string(storage_str):
    storage_str = storage_str.lower()
    if 'tb' in storage_str:
        return int(float(storage_str.replace('tb', '').strip()) * 1000 * 1000)
    elif 'gb' in storage_str:
        return int(float(storage_str.replace('gb', '').strip()) * 1000)
    elif 'mb' in storage_str:
        return int(float(storage_str.replace('mb', '').strip()))
    elif 'kb' in storage_str:
        return int(float(storage_str.replace('kb', '').strip()) / 1000)
    elif 'bytes' in storage_str or storage_str == '0':
        return 0.0
    else:
        raise ValueError(f"Unknown storage unit in string: {storage_str}")