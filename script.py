import logging
import requests
from bs4 import BeautifulSoup
import json
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Телеграм-бот токен и ID чата
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# URL страницы с товаром
URL = "https://www.worten.pt/produtos/aspirador-sem-saco-bosch-bgs7sil1-pro-silence-64-db-deposito-3-l-7363652"

# Файл для хранения цены
PRICE_FILE = "price.json"

# Функция для получения текущей цены
def get_price():
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    session.headers.update(headers)
    response = session.get(URL)
    soup = BeautifulSoup(response.text, "html.parser")

    price_meta = soup.find("meta", itemprop="price")
    print("!!!!!!!!!!!!" + price_meta)
    # logging.debug(soup.prettify())
    if price_meta:
        price = price_meta["content"]
        print(f"Цена: {price} EUR!")
        return price
    else:
        print("Цена не найдена!")
        return None

# Функция для отправки сообщения в Telegram
async def send_telegram_message(context: CallbackContext, message: str):
    await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# Функция для проверки цены
async def check_price(context: CallbackContext):
    current_price = get_price()
    if current_price is None:
        print("Не удалось получить цену.")
        return

    # Проверяем, есть ли сохранённая цена
    if os.path.exists(PRICE_FILE):
        with open(PRICE_FILE, "r") as file:
            saved_data = json.load(file)
            saved_price = saved_data.get("price")
    else:
        saved_price = None

    # Если цена не изменилась, отправляем сообщение
    if saved_price is not None and current_price == saved_price:
        await send_telegram_message(context, f"Цена не изменилась: {current_price}€")

    # Обновляем сохранённую цену
    with open(PRICE_FILE, "w") as file:
        json.dump({"price": current_price}, file)

# Команда /price
async def price_command(update: Update, context: CallbackContext):
    price = get_price()
    if price:
        await update.message.reply_text(f"Текущая цена: {price} EUR")
    else:
        print(f"TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN}")
        print(f"TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")
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

    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
