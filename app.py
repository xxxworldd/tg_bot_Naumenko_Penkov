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
                username TEXT
            );
            ''')
            conn.commit()

    def get_all_users(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, chat_id, username FROM users;')
                users = cursor.fetchall()  # Получаем все записи пользователей
                return users
        except sqlite3.Error as e:
            print(f"Ошибка при извлечении пользователей: {e}")
            return []

# Flask-приложение
app = Flask(__name__)
db = DBManager()  # Инициализация базы данных
db.create_tables()

# Добавление тестовых пользователей (выполните один раз для добавления тестовых данных)
def add_test_users():
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO users (chat_id, username) VALUES (?, ?);
        ''', (123456789, 'testuser1'))
        cursor.execute('''
        INSERT INTO users (chat_id, username) VALUES (?, ?);
        ''', (987654321, 'testuser2'))
        conn.commit()

# Вызовите эту функцию один раз для добавления тестовых пользователей
# add_test_users()

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
    # Получаем список пользователей из базы данных
    users = db.get_all_users()
    # Отправляем данные в шаблон
    return render_template('index.html', users=users)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083)
