import asyncio

import config
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date, datetime, timedelta
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
import cv2

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
message_date = datetime.today().date() - timedelta(days=1)

class Parser:
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.options = Options()
        self.options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=self.options)

    @staticmethod
    def is_message():
        date = datetime.today().date()
        global message_date
        if date != message_date:
            message_date = date
            return False
        return True

    async def login(self):
        self.driver.get('https://xms.miatel.ru/login?redirect=%2F')
        wait = WebDriverWait(self.driver, 15).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'v-form'))
        )
        username_field = self.driver.find_element(By.CSS_SELECTOR, '[type="text"]')
        password_field = self.driver.find_element(By.CSS_SELECTOR, '[type="password"]')
        while len(username_field.get_attribute('value')) != 23:
            username_field.clear()
            username_field.send_keys(self.user)
        while len(password_field.get_attribute('value')) != 20:
             password_field.clear()
             password_field.send_keys(self.password)
        submit_button = self.driver.find_element(By.CSS_SELECTOR, '[type="submit"]')
        submit_button.click()
        wait = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[href="/balance"]'))
        )

    async def get_balance(self):
        self.driver.get('https://xms.miatel.ru/balance')
        wait = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'td.text-right > div > span'))
        )
        balance_elem = self.driver.find_element(By.CSS_SELECTOR, 'td.text-right > div > span').text
        rub, coins = balance_elem[:-2].split(',')
        coins = f"0.{coins}"
        rub = ''.join(rub.split())
        balance = int(rub) + float(coins)
        return balance

    async def check_sms(self):
        self.driver.get('https://xms.miatel.ru/history')
        wait = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody :first-child td'))
        )
        wait = WebDriverWait(self.driver, 15).until_not(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'tbody :first-child td'), 'Запись загружается...')
        )
        date_elem = self.driver.find_element(By.CSS_SELECTOR, 'tbody :first-child td').text
        if date_elem == "Отсутствуют данные":
            return False
        sms_date = datetime.strptime(date_elem, '%d.%m.%Y %H:%M').date()
        now = datetime.now().date()
        return sms_date == now

    async def get_captcha_symbols(self):
        text = ''
        while len(text) != 4:
            self.driver.get("https://lcab.smsprofi.ru/cabinet/login")
            wait = WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '[src*="/cabinet/api/clientOrGuest"]'))
            )
            captcha_element = self.driver.find_element(By.CSS_SELECTOR, '[src*="/cabinet/api/clientOrGuest"]')
            captcha_element.screenshot("captcha.png")
            captcha_image = Image.open("captcha.png")
            captcha_image = captcha_image.resize((300, 100))
            enhancer = ImageEnhance.Contrast(captcha_image)
            captcha_image = enhancer.enhance(5) # Увеличение контрастности в 2 раза
            captcha_image.save("captcha.png")
            screenshot = cv2.imread("captcha.png", cv2.IMREAD_GRAYSCALE)
            blurred = cv2.GaussianBlur(screenshot, (5, 5), 0)
            _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            cv2.imwrite("captcha.png", thresholded)
            text = Parser.decrypt("captcha.png")

        return text

    async def login_smsprofi(self, text):
        login = self.driver.find_element(By.ID, 'login')
        password = self.driver.find_element(By.ID, 'password')
        captcha = self.driver.find_element(By.CSS_SELECTOR, '[class*="mr-2"] input')
        login.send_keys('yr')
        password.send_keys('T?VxEZm#KqMRw6C+6>#Co!YU')
        captcha.send_keys(text)
        enter = self.driver.find_element(By.CSS_SELECTOR,
                                         '[class="el-form el-form--label-top"] [type="submit"]')
        enter.click()
        try:
            wait = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '[class*="org-descr"] span:first-child'))
            )
            balance = self.driver.find_element(By.CSS_SELECTOR, '[class*="org-descr"] span:first-child').text
            return float(balance)
        except:
            self.driver.refresh()
            return False

    @staticmethod
    def decrypt(image):
        data = pytesseract.image_to_string(image, config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789')
        text = ''.join(data.split())
        text = ''.join(text.split('/n'))
        return text

    async def quit(self):
        self.driver.quit()