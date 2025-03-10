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
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")


# Убедитесь, что ChromeDriver установлен
service = Service(ChromeDriverManager().install())


# Функция для получения цены через Selenium
def get_price():
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        logging.info("Open page...")
        driver.get(URL)
        logging.info("Page loaded, waiting for the price element...")

        # Ждём, пока появится meta-тег с ценой
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                                            'html body.w-session-channel-WEB.w-session-mode-site div#__nuxt div div div div div section.product-heading div.wrapper div.product-heading__main-container div.product-heading__buy-boxes div.buy-box div div.badges-container--grid.badges-container div.product-price-info span.price--lg.price--mixed.price--B.price span.price__container span.price__numbers--bold.price__numbers.notranslate.raised-decimal span.value'))
        )
        price_element2 = driver.find_element(By.CSS_SELECTOR, 'html body.w-session-channel-WEB.w-session-mode-site div#__nuxt div div div div div section.product-heading div.wrapper div.product-heading__main-container div.product-heading__buy-boxes div.buy-box div div.badges-container--grid.badges-container div.product-price-info span.price--lg.price--mixed.price--B.price span.price__container span.price__numbers--bold.price__numbers.notranslate.raised-decimal span.value')
        logging.info(f"Price element HTML2: {price_element2.get_attribute('outerHTML')}")
        price_element = driver.find_element(By.CSS_SELECTOR, 'meta[itemprop="price"]')
        logging.info(f"Price element HTML1: {price_element.get_attribute('outerHTML')}")
        price = price_element.get_attribute("content")
        logging.info(f"Price found: {price} EUR")

        # Получаем HTML страницы
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
        driver.quit()  # Закрываем браузер


# Функция для отправки сообщения в Telegram
async def send_telegram_message(context: CallbackContext, message: str):
    await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


# Функция для проверки цены
async def check_price(context: CallbackContext):
    current_price = get_price()
    if current_price is None:
        logging.warning("Failed to get the price.")
        return

    # Проверяем, есть ли сохранённая цена
    if os.path.exists(PRICE_FILE):
        with open(PRICE_FILE, "r") as file:
            saved_data = json.load(file)
            saved_price = saved_data.get("price")
    else:
        saved_price = None

    # Если цена изменилась — уведомляем
    if saved_price is not None and current_price != saved_price:
        await send_telegram_message(context, f"Price is changed: {saved_price}€ → {current_price}€")

    # Обновляем сохранённую цену
    with open(PRICE_FILE, "w") as file:
        json.dump({"price": current_price}, file)


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
