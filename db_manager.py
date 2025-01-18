import sqlite3
import random
import telebot

TOKEN = '7749208433:AAGNzzljarO0UAU2akle7muZY-N2N9Gd5pA'
bot = telebot.TeleBot(TOKEN)

class DBManager:
    def __init__(self, db_path='bot_database.db'):
        self.db_path = db_path
        self.create_tables()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                role TEXT
            );
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_state (
                chat_id INTEGER PRIMARY KEY,
                game_active BOOLEAN DEFAULT 0,
                target_number INTEGER,
                FOREIGN KEY(chat_id) REFERENCES users(chat_id)
            );
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(chat_id) REFERENCES users(chat_id)
            );
            ''')
            conn.commit()

    def register_user(self, chat_id, username):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users')
                count = cursor.fetchone()[0]

            role = 'руководитель' if count == 0 else 'управляющий' if count == 1 else 'гость'

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT OR IGNORE INTO users (chat_id, username, role)
                VALUES (?, ?, ?);
                ''', (chat_id, username, role))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка регистрации пользователя: {e}")

    def save_message(self, chat_id, message):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO messages (chat_id, message)
                VALUES (?, ?);
                ''', (chat_id, message))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении сообщения: {e}")

    def start_game(self, chat_id):
        target_number = random.randint(1, 100)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO game_state (chat_id, game_active, target_number)
                VALUES (?, ?, ?);
                ''', (chat_id, 1, target_number))  # Устанавливаем game_active в 1
                conn.commit()
            print(f"Игра для {chat_id} началась, загаданное число: {target_number}")  # Отладка
            return target_number
        except sqlite3.Error as e:
            print(f"Ошибка при начале игры: {e}")
            return None

    def stop_game(self, chat_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE game_state
                SET game_active = 0
                WHERE chat_id = ?;
                ''', (chat_id,))
                conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при остановке игры: {e}")

    def get_game_state(self, chat_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT game_active, target_number FROM game_state
                WHERE chat_id = ?;
                ''', (chat_id,))
                row = cursor.fetchone()
                if row:
                    # Преобразуем sqlite3.Row в словарь
                    game_state = dict(row)
                    print(f"Состояние игры для {chat_id}: {game_state}")  # Печатаем содержимое игры
                    return game_state
                return None
        except sqlite3.Error as e:
            print(f"Ошибка при получении состояния игры: {e}")
            return None

    def get_all_game_states(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM game_state;')
                rows = cursor.fetchall()
                print("Все состояния игры:", rows)
                return rows
        except sqlite3.Error as e:
            print(f"Ошибка при получении всех состояний игры: {e}")
            return None


# Инициализация базы данных
db = DBManager()

# Обработчики команд бота
@bot.message_handler(commands=['start'])
def send_greeting(message):
    chat_id = message.chat.id
    username = message.from_user.username or "Пользователь"
    db.register_user(chat_id, username)
    bot.send_message(chat_id, "Привет! Вы зарегистрированы.")
    db.save_message(chat_id, "Пользователь зарегистрирован.")

@bot.message_handler(commands=['game'])
def start_game(message):
    chat_id = message.chat.id
    if db.get_game_state(chat_id):
        bot.send_message(chat_id, "Игра уже запущена! Угадайте число.")
    else:
        target_number = db.start_game(chat_id)
        if target_number:
            bot.send_message(chat_id, f"Игра началась! Угадайте число от 1 до 100. Напишите 'стоп', чтобы выйти.")
        else:
            bot.send_message(chat_id, "Ошибка при запуске игры. Попробуйте позже.")

@bot.message_handler(func=lambda message: db.get_game_state(message.chat.id) and db.get_game_state(message.chat.id)['game_active'])
def play_game(message):
    chat_id = message.chat.id
    state = db.get_game_state(chat_id)

    print(f"Состояние игры для {chat_id}: {state}")  # Отладочное сообщение

    if state is None or not state['game_active']:
        bot.send_message(chat_id, "Игра не активна. Запустите игру с командой /game.")
        return

    if message.text.lower() == "стоп":
        db.stop_game(chat_id)
        bot.send_message(chat_id, "Игра остановлена.")
        return

    try:
        guess = int(message.text)
        if guess < state['target_number']:
            bot.send_message(chat_id, "Загаданное число больше.")
        elif guess > state['target_number']:
            bot.send_message(chat_id, "Загаданное число меньше.")
        else:
            bot.send_message(chat_id, "Поздравляю! Вы угадали число.")
            db.stop_game(chat_id)  # Игра завершена
    except ValueError:
        bot.send_message(chat_id, "Введите число или напишите 'стоп' для завершения игры.")

@bot.message_handler(commands=['chatid'])
def send_chat_id(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, f"Ваш chat_id: {chat_id}")

@bot.message_handler(commands=['all_game_states'])
def show_all_game_states(message):
    chat_id = message.chat.id
    game_states = db.get_all_game_states()
    if game_states:
        response = "\n".join([f"chat_id: {state['chat_id']}, game_active: {state['game_active']}, target_number: {state['target_number']}" for state in game_states])
        bot.send_message(chat_id, response)
    else:
        bot.send_message(chat_id, "Не удалось получить состояния игры.")

# Запуск бота
bot.polling()
