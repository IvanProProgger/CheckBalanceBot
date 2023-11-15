from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import date, datetime, timedelta
import asyncio

class Parser:
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.options = Options()
        self.options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=self.options)

    async def login(self):
        self.driver.get('https://xms.miatel.ru/login?redirect=%2F')
        username_field = self.driver.find_element(By.CSS_SELECTOR, '[type="text"]')
        password_field = self.driver.find_element(By.CSS_SELECTOR, '[type="password"]')
        while username_field.get_attribute('value') != 'npronyushkin@tennisi.it':
            username_field.send_keys(self.user)
        while len(password_field.get_attribute('value')) != 20:
            password_field.clear()
            password_field.send_keys(self.password)
        submit_button = self.driver.find_element(By.CSS_SELECTOR, '[type="submit"]')
        submit_button.click()
        wait = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[href="/balance"]')))

    async def get_balance(self):
        self.driver.get('https://xms.miatel.ru/balance')
        wait = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'td.text-right > div > span')))
        balance_elem = self.driver.find_element(By.CSS_SELECTOR, 'td.text-right > div > span').text
        rub, coins = balance_elem[:-2].split(',')
        coins = f"0.{coins}"
        rub = ''.join(rub.split())
        balance = int(rub) + float(coins)
        return balance

    async def checkSms(self):
        self.driver.get('https://xms.miatel.ru/history')
        wait = WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'tbody :first-child td')))
        date_elem = self.driver.find_element(By.CSS_SELECTOR, 'tbody :first-child td').text
        sms_date = datetime.strptime(date_elem, '%d.%m.%Y %H:%M').date()
        now = datetime.now().date()
        return sms_date == now

    async def check_date(self):
        today = date.today() - timedelta(days=1)
        def inner():
            nonlocal today
            current_date = datetime.today().date()
            if current_date != today:  # Если текущая дата не совпадает с сохраненной датой
                today = current_date  # Обновляем сохраненную дату
                return False
            return True
        return inner

    async def quit(self):
        self.driver.quit()

