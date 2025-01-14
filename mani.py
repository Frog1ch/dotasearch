import time
from flask import Flask, request, jsonify
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import threading

app = Flask(__name__)

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

@app.route('/save', methods=['POST'])
def save():
    """Сохранение данных пользователя."""
    data = request.json
    user_id = data.get('userId')
    user_data = data.get('userData')
    
    # Сохранение данных пользователя
    save_user_data(user_id, user_data)
    
    # Возвращаем список активных пользователей
    return jsonify({'users': get_users()})

@app.route('/get_users', methods=['GET'])
def get_active_users():
    """Получение списка активных пользователей."""
    return jsonify({'users': get_users()})

def start(update: Update, context: CallbackContext):
    """Обработка команды /start."""
    url = "https://frog1ch.github.io/dotasearch/"  # URL вашего мини-приложения
    button = InlineKeyboardButton("Open Mini App", url=url)
    keyboard = InlineKeyboardMarkup([[button]])
    update.message.reply_text("Нажмите на кнопку, чтобы открыть мини-приложение:", reply_markup=keyboard)

def main():
    # Замените на токен вашего бота
    token = "YOUR_BOT_TOKEN"
    updater = Updater(token)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    app.run(port=5001)
    main()
