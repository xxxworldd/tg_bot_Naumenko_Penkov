import sqlite3
from flask import Flask, render_template, g

# Создание и управление базой данных
class DBManager:
    def __init__(self, db_path='bot_database.db'):
        self.db_path = db_path

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Удобный формат для работы с результатами
        return conn

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                role TEXT DEFAULT 'Пользователь'
            );
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                chat_id INTEGER PRIMARY KEY,
                number INTEGER,
                won BOOLEAN DEFAULT 0
            );
            ''')
            conn.commit()

    def get_all_users(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, chat_id, username, role FROM users;')
                users = cursor.fetchall()  # Получаем все записи пользователей
                return users
        except sqlite3.Error as e:
            print(f"Ошибка при извлечении пользователей: {e}")
            return []

    def get_user_count(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users;')
                count = cursor.fetchone()[0]
                return count
        except sqlite3.Error as e:
            print(f"Ошибка при извлечении количества пользователей: {e}")
            return 0

    def get_won_games_count(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM games WHERE won = 1;')
                count = cursor.fetchone()[0]
                return count
        except sqlite3.Error as e:
            print(f"Ошибка при извлечении количества выигранных игр: {e}")
            return 0

# Flask-приложение
app = Flask(__name__)
db = DBManager()  # Инициализация базы данных
db.create_tables()

@app.before_request
def before_request():
    g.db = db.get_connection()

@app.teardown_appcontext
def teardown_request(exception):
    db_conn = g.pop('db', None)
    if db_conn:
        db_conn.close()

@app.route('/')
def index():
    # Получаем статистику
    user_count = db.get_user_count()
    won_games_count = db.get_won_games_count()

    # Получаем список пользователей
    users = db.get_all_users()

    # Отправляем данные в шаблон
    return render_template('index.html', users=users, user_count=user_count, won_games_count=won_games_count)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8086)
