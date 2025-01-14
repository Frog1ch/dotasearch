from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# Временная база данных
users_data = {}

# Время хранения данных (например, 30 минут)
EXPIRATION_TIME = 30 * 60  # 30 минут

# Функция для очистки устаревших данных
def clean_expired_data():
    current_time = time.time()
    to_delete = [user_id for user_id, data in users_data.items() if current_time - data['timestamp'] > EXPIRATION_TIME]
    for user_id in to_delete:
        del users_data[user_id]

# Функция для сохранения данных пользователя
def save_user_data(user_id, data):
    users_data[user_id] = {
        "mmr": data.get("mmr"),
        "role": data.get("role"),
        "server": data.get("server"),
        "timestamp": time.time()  # Время последнего обновления данных
    }

# Функция для получения списка активных пользователей
def get_users():
    clean_expired_data()  # Очистка устаревших данных перед получением
    return [{
        "user_id": user_id,
        "mmr": data["mmr"],
        "role": data["role"],
        "server": data["server"]
    } for user_id, data in users_data.items()]

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

if __name__ == "__main__":
    app.run(port=5001)
