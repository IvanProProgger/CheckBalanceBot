import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date, datetime, timedelta

message = datetime.today().date() - timedelta(days=1)

class Parser:
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.options = Options()
        self.options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=self.options)

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
        self.driver.implicitly_wait(2)
        date_elem = self.driver.find_element(By.CSS_SELECTOR, 'tbody :first-child td').text
        if date_elem == "Отсутствуют данные":
            return False
        sms_date = datetime.strptime(date_elem, '%d.%m.%Y %H:%M').date()
        now = datetime.now().date()
        return sms_date == now

    @staticmethod
    def is_message(date):
        global message
        if date != message:
            message = date
            return False
        return True

    async def quit(self):
        self.driver.quit()