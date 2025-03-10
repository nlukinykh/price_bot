import logging
import json
import os
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

# Настройка Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # Без интерфейса
chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Маскируем Selenium
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

service = Service(ChromeDriverManager().install())

# Функция для получения цены через Selenium
def get_price():
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        logging.info("Открываем страницу товара...")
        driver.get(URL)

        # Ждём, пока появится meta-тег с ценой
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'meta[itemprop="price"]'))
        )

        # Получаем HTML страницы
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        logging.info("Страница загружена, ищем цену...")
        logging.debug(soup.prettify()[:2000])  # Вывод части HTML для отладки

        price_meta = soup.find("meta", itemprop="price")

        if price_meta:
            price = price_meta["content"]
            logging.info(f"Цена найдена: {price} EUR")
            return price
        else:
            logging.warning("Цена не найдена!")
            return None

    except Exception as e:
        logging.error(f"Ошибка при получении цены: {e}")
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
        logging.warning("Не удалось получить цену.")
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
        await send_telegram_message(context, f"Цена изменилась: {saved_price}€ → {current_price}€")

    # Обновляем сохранённую цену
    with open(PRICE_FILE, "w") as file:
        json.dump({"price": current_price}, file)

# Команда /price
async def price_command(update: Update, context: CallbackContext):
    price = get_price()
    if price:
        await update.message.reply_text(f"Текущая цена: {price} EUR")
    else:
        logging.warning("Ошибка при получении цены!")
        await update.message.reply_text("Не удалось получить цену :(")

# Команда /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Я бот.")

# Запуск бота
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price_command))

    logging.info("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()