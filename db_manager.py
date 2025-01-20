import sqlite3

class DBManager:
    def __init__(self, db_name="bot_database.db"):
        # Подключение к базе данных
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self._create_tables()

    def _create_tables(self):
        """
        Создает таблицы для хранения информации о текущих играх и пользователях.
        Обновляет таблицу games, если необходимо добавить колонку 'won'.
        """
        # Создаем таблицу для пользователей, если она еще не существует
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,      -- Уникальный ID пользователя
                role TEXT                   -- Роль пользователя (например, Пользователь, Руководитель, Управляющий)
            )
        """)

        # Создаем таблицу для игр, если она еще не существует
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                chat_id INTEGER PRIMARY KEY,  -- Уникальный ID чата
                number INTEGER,              -- Загаданное число
                won BOOLEAN DEFAULT 0        -- Было ли выиграно (0 - не выиграна, 1 - выиграна)
            )
        """)

        # Добавляем колонку 'won', если она еще не существует
        self._add_column_if_not_exists("games", "won", "BOOLEAN DEFAULT 0")

        self.connection.commit()

    def _add_column_if_not_exists(self, table_name, column_name, column_definition):
        """
        Добавляет колонку в таблицу, если она еще не существует.
        """
        try:
            self.cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
            self.connection.commit()
        except sqlite3.OperationalError:
            # Если колонка уже существует, игнорируем ошибку
            pass

    def add_user(self, user_id, role="Пользователь"):
        """
        Добавляет нового пользователя в базу данных, если он ещё не существует.
        """
        self.cursor.execute("INSERT OR IGNORE INTO users (id, role) VALUES (?, ?)", (user_id, role))
        self.connection.commit()

    def get_user_count(self):
        """
        Возвращает количество пользователей.
        """
        self.cursor.execute("SELECT COUNT(*) FROM users")
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def start_game(self, chat_id, number):
        """
        Начинает новую игру, сохраняя загаданное число для чата.
        """
        self.cursor.execute("INSERT OR REPLACE INTO games (chat_id, number) VALUES (?, ?)", (chat_id, number))
        self.connection.commit()

    def get_game_number(self, chat_id):
        """
        Возвращает загаданное число для текущей игры в чате.
        """
        self.cursor.execute("SELECT number FROM games WHERE chat_id = ?", (chat_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def stop_game(self, chat_id, won=False):
        """
        Завершает игру, помечая ее как выигранную или невыигранную.
        """
        self.cursor.execute("UPDATE games SET won = ? WHERE chat_id = ?", (won, chat_id))
        self.connection.commit()

    def get_all_games_count(self):
        """
        Возвращает количество всех игр.
        """
        self.cursor.execute("SELECT COUNT(*) FROM games")
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def get_won_games_count(self):
        """
        Возвращает количество выигранных игр.
        """
        self.cursor.execute("SELECT COUNT(*) FROM games WHERE won = 1")
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def close(self):
        """
        Закрывает соединение с базой данных.
        """
        self.connection.close()
