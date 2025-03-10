import logging
import json
import os

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext


logging.basicConfig(level=logging.INFO)

# Телеграм-бот токен и ID чата
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# URL страницы с товаром
URL = "https://www.worten.pt/produtos/aspirador-sem-saco-bosch-bgs7sil1-pro-silence-64-db-deposito-3-l-7363652"

# Файл для хранения цены
PRICE_FILE = "price.json"

# Настройка Firefox
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")


# Убедитесь, что ChromeDriver установлен
service = Service(ChromeDriverManager().install())


import logging
import json
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Логирование
logging.basicConfig(level=logging.INFO)

# Телеграм-бот токен и ID чата
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# URL страницы с товаром
URL = "https://www.worten.pt/produtos/aspirador-sem-saco-bosch-bgs7sil1-pro-silence-64-db-deposito-3-l-7363652"

# Файл для хранения цены
PRICE_FILE = "price.json"

# Настройка Chrome
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

service = Service(ChromeDriverManager().install())

def get_price():
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        logging.info("Open page...")
        driver.get(URL)
        logging.info("Page loaded, waiting for the price element...")

        time.sleep(5)

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'meta[itemprop="price"]'))
        )

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        price_meta = soup.find("meta", {"itemprop": "price"})

        if price_meta:
            price = price_meta["content"]
            logging.info(f"Price is found: {price} EUR")
            return price
        else:
            logging.warning("Price is not found!")
            return None

    except Exception as e:
        logging.error(f"Got an error by getting a price: {e}")
        return None

    finally:
        driver.quit()

# Команда /price
async def price_command(update: Update, context: CallbackContext):
    price = get_price()
    if price:
        await update.message.reply_text(f"Current price: {price} EUR")
    else:
        logging.warning("Error when receiving the price!")
        await update.message.reply_text("Failed to get the price :(")


# Команда /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Hello, I'm bot")


# Запуск бота
def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting the bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price_command))

    logging.info("Bot is running!")
    app.run_polling()


if __name__ == "__main__":
    main()
