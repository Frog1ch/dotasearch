import flask31
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import sys
import time
import threading

# Временная база данных
temp_db = {}

# Время хранения данных (например, 30 минут)
EXPIRATION_TIME = 30 * 60

def clean_expired_data():
    """Очистка базы данных от устаревших записей."""
    while True:
        current_time = time.time()
        to_delete = [user_id for user_id, data in temp_db.items() if current_time - data['timestamp'] > EXPIRATION_TIME]
        for user_id in to_delete:
            del temp_db[user_id]
        time.sleep(60)  # Проверяем каждые 60 секунд

# Фоновый поток для очистки
threading.Thread(target=clean_expired_data, daemon=True).start()

def start(update: Update, context: CallbackContext):
    """Обработка команды /start."""
    url = "https://your-miniapp-url.com"  # URL вашего мини-приложения
    button = InlineKeyboardButton("Open Mini App", url=url)
    keyboard = InlineKeyboardMarkup([[button]])
    update.message.reply_text("Нажмите на кнопку, чтобы открыть мини-приложение:", reply_markup=keyboard)

    context.bot.stop()
    sys.exit(0)


def save_user_data(user_id, data):
    """Сохранение данных пользователя во временную базу."""
    temp_db[user_id] = {
        "mmr": data.get("mmr"),
        "role": data.get("role"),
        "server": data.get("server"),
        "timestamp": time.time()
    }

def get_users():
    """Получение списка активных пользователей."""
    return [
        {
            "user_id": user_id,
            "mmr": data["mmr"],
            "role": data["role"],
            "server": data["server"]
        }
        for user_id, data in temp_db.items()
    ]

def main():
    # Замените на токен вашего бота
    token = "7603859590:AAEeyA89ejqEYNimlgmcRSZbQo3B2t2KQHQOKEN"
    updater = Updater(token)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()