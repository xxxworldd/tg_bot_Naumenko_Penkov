import telebot
import random
from db_manager import DBManager

TOKEN = '7749208433:AAGNzzljarO0UAU2akle7muZY-N2N9Gd5pA'
bot = telebot.TeleBot(TOKEN)

# Подключение к базе данных
db = DBManager()

# Приветствия
greetings = [
    "Здарова!",
    "Ку!",
    "Доброго времени суток!",
    "Приветствую!",
    "Ассаламу алейкум!"
]

# Стандартные команды
@bot.message_handler(commands=['start'])
def send_greeting(message):
    chat_id = message.chat.id
    username = message.chat.username or "Пользователь"

    # Регистрация пользователя и назначение роли по умолчанию (гость)
    db.register_user(chat_id, username)
    db.set_role(chat_id, 'гость')

    db.save_message(chat_id, "Приветствие отправлено.")
    print(f"Отправлено приветствие для {chat_id}")

    # Отправляем приветствие
    bot.send_message(chat_id, random.choice(greetings))


@bot.message_handler(commands=['game'])
def start_game(message):
    chat_id = message.chat.id
    print(f"Пользователь {chat_id} запустил игру.")  # Для отладки

    # Проверяем состояние игры
    game_state = db.get_game_state(chat_id)
    if game_state and game_state['game_active'] == 1:
        bot.send_message(chat_id, "Игра уже запущена! Угадайте число.")
    else:
        target_number = db.start_game(chat_id)
        if target_number:
            bot.send_message(chat_id, "Игра началась! Угадайте число от 1 до 100. Напишите 'стоп', чтобы выйти.")
        else:
            bot.send_message(chat_id, "Ошибка при запуске игры. Попробуйте позже.")


# Обработчик чисел, которые пользователь вводит во время игры
@bot.message_handler(func=lambda message: db.get_game_state(message.chat.id) is not None)
def play_game(message):
    chat_id = message.chat.id
    game_state = db.get_game_state(chat_id)

    # Проверяем, активна ли игра
    if not game_state or not game_state.get("game_active"):
        bot.send_message(chat_id, "Игра не активна. Запустите игру с командой /game.")
        return

    if message.text.lower() == 'стоп':
        db.stop_game(chat_id)
        bot.send_message(chat_id, "Игра завершена.")
        db.save_message(chat_id, "Игра остановлена.")
        return

    try:
        guess = int(message.text)  # Проверяем вводимое число
        target_number = game_state['target_number']  # Получаем загаданное число из базы данных
        print(f"Пользователь {chat_id} ввел число {guess}. Загаданное число: {target_number}.")

        if guess < target_number:
            bot.send_message(chat_id, "Загаданное число больше. Попробуйте снова.")
        elif guess > target_number:
            bot.send_message(chat_id, "Загаданное число меньше. Попробуйте снова.")
        else:
            bot.send_message(chat_id, "Поздравляю! Вы угадали число!")
            db.stop_game(chat_id)  # Завершаем игру в базе данных
            db.save_message(chat_id, "Игра завершена.")
            bot.send_message(chat_id, "Игра завершена. Используйте /game для новой игры.")
    except ValueError:
        bot.send_message(chat_id, "Введите корректное число или напишите 'стоп' для завершения игры.")
    except Exception as e:
        bot.send_message(chat_id, "Произошла ошибка. Попробуйте снова.")
        print(f"Ошибка в play_game: {e}")


# Команды для завершения игры
@bot.message_handler(commands=['stop'])
def stop_game(message):
    chat_id = message.chat.id
    db.stop_game(chat_id)
    bot.send_message(chat_id, "Игра завершена.")
    db.save_message(chat_id, "Игра остановлена.")


# Команда для получения chat_id
@bot.message_handler(commands=['chatid'])
def send_chat_id(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, f"Ваш chat_id: {chat_id}")
    db.save_message(chat_id, f"Пользователь запросил chat_id: {chat_id}")
    print(f"Chat ID: {chat_id}")  # Отладка, чтобы проверить, что chat_id получен правильно


# Команда для получения роли пользователя
@bot.message_handler(commands=['role'])
def get_role(message):
    chat_id = message.chat.id
    role = db.get_role(chat_id)
    if role:
        bot.send_message(chat_id, f"Ваша роль: {role}")
    else:
        bot.send_message(chat_id, "Вы не зарегистрированы в системе.")


# Команда для изменения роли пользователем (только для администратора)
@bot.message_handler(commands=['setrole'])
def set_role(message):
    chat_id = message.chat.id
    admin_chat_id = 865173045  # Здесь укажите свой chat_id, чтобы только вы могли изменять роли

    if chat_id == admin_chat_id:
        parts = message.text.split()
        if len(parts) == 3:
            target_chat_id = int(parts[1])
            role_name = parts[2]

            valid_roles = ['гость', 'управляющий', 'руководитель']
            if role_name not in valid_roles:
                bot.send_message(chat_id, "Недопустимая роль.")
                return

            db.set_role(target_chat_id, role_name)
            bot.send_message(chat_id, f"Роль пользователя {target_chat_id} изменена на {role_name}.")
        else:
            bot.send_message(chat_id, "Неверный формат команды. Используйте /setrole <chat_id> <role>")
    else:
        bot.send_message(chat_id, "У вас нет прав для изменения ролей.")


# Основной цикл бота
bot.polling(none_stop=True, interval=3, timeout=60)
