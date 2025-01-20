import telebot
import random
from db_manager import DBManager

# Токен вашего бота от BotFather
TOKEN = "7749208433:AAGNzzljarO0UAU2akle7muZY-N2N9Gd5pA"

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Инициализация базы данных
db = DBManager()

# Пример назначения роли по chat_id
roles = {
    865173045: "Руководитель",  # Чат с ID 865173045 - роль "Руководитель"
    830832627: "Управляющий",   # Чат с ID 830832627 - роль "Управляющий"
}

# Получаем роль для chat_id
def get_role_for_chat(chat_id):
    return roles.get(chat_id, "Пользователь")  # Если chat_id нет в словаре, возвращаем "Пользователь"

# Проверка, является ли пользователь "Руководителем"
def is_leader(chat_id):
    return get_role_for_chat(chat_id) == "Руководитель"

# Словарь для хранения статуса редактирования
edit_response_status = {}

# Команда /start
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    role = get_role_for_chat(chat_id)

    bot.reply_to(message, f"Привет! Я бот, который загадывает числа. Ваша роль: {role}. Введи /game, чтобы начать игру!")

# Команда /game
@bot.message_handler(commands=['game'])
def game_command(message):
    chat_id = message.chat.id
    role = get_role_for_chat(chat_id)

    if role == "Пользователь":
        bot.reply_to(message, "У вас нет прав для начала игры. Только Руководитель и Управляющий могут начать игру.")
        return

    game_number = db.get_game_number(chat_id)

    if game_number:
        bot.reply_to(message, "Игра уже начата! Угадывай число или введи /stop, чтобы завершить игру.")
    else:
        number = random.randint(1, 100)
        db.start_game(chat_id, number)
        bot.reply_to(message, "Я загадал число от 1 до 100. Попробуй угадать!")

# Команда /stop
@bot.message_handler(commands=['stop'])
def stop_command(message):
    chat_id = message.chat.id
    role = get_role_for_chat(chat_id)

    if role == "Пользователь":
        bot.reply_to(message, "У вас нет прав для остановки игры. Только Руководитель и Управляющий могут остановить игру.")
        return

    game_number = db.get_game_number(chat_id)

    if game_number:
        db.stop_game(chat_id)
        bot.reply_to(message, "Игра завершена. Если хочешь сыграть снова, введи /game.")
    else:
        bot.reply_to(message, "Ты пока не начал игру. Введи /game, чтобы начать!")

# Команда /role
@bot.message_handler(commands=['role'])
def role_command(message):
    chat_id = message.chat.id
    role = get_role_for_chat(chat_id)

    bot.reply_to(message, f"Ваша роль: {role}")

# Команда /chatid
@bot.message_handler(commands=['chatid'])
def chatid_command(message):
    chat_id = message.chat.id
    role = get_role_for_chat(chat_id)

    bot.reply_to(message, f"ID этого чата: {chat_id}\nВаша роль: {role}")

# Команда /editresponse (Только для "Управляющего" и "Руководителя")
@bot.message_handler(commands=['editresponse'])
def edit_response(message):
    chat_id = message.chat.id
    role = get_role_for_chat(chat_id)

    if not (get_role_for_chat(chat_id) in ["Управляющий", "Руководитель"]):  # Проверка, является ли пользователь "Управляющим" или "Руководителем"
        bot.reply_to(message, "У вас нет прав для редактирования ответов бота. Только Руководитель и Управляющий могут редактировать.")
        return

    # Помечаем, что этот чат сейчас ожидает новый ответ
    edit_response_status[chat_id] = True
    bot.reply_to(message, "Введите новый ответ для игры: (например, 'Я загадал число, попробуй угадать!')")

# Обработка новых сообщений для редактирования ответа
@bot.message_handler(func=lambda message: message.chat.id in edit_response_status and edit_response_status[message.chat.id])
def handle_new_response(message):
    chat_id = message.chat.id

    # Получаем новый ответ
    new_response = message.text

    # Здесь можно добавить логику для сохранения нового ответа в базе данных или в другом месте
    # Например, можно обновить ответ в базе данных, если нужно

    # Обновляем статус редактирования
    edit_response_status[chat_id] = False  # Ожидание нового ответа завершено

    bot.reply_to(message, f"Ответ для игры обновлен: {new_response}")

# Команда /stats (Только для "Руководителя")
@bot.message_handler(commands=['stats'])
def stats_command(message):
    chat_id = message.chat.id
    role = get_role_for_chat(chat_id)

    if not is_leader(chat_id):  # Проверка, является ли пользователь "Руководителем"
        bot.reply_to(message, "У вас нет прав для получения статистики. Только Руководитель может получить статистику.")
        return

    # Получаем статистику
    total_users = db.get_user_count()  # Количество пользователей
    total_games = db.get_all_games_count()  # Количество начатых игр
    won_games = db.get_won_games_count()  # Количество выигранных игр

    # Логируем статистику
    print(f"Количество пользователей: {total_users}")
    print(f"Количество начатых игр: {total_games}")
    print(f"Количество выигранных игр: {won_games}")

    # Отправляем статистику пользователю
    bot.reply_to(message, f"Общая статистика:\n"
                          f"Количество пользователей: {total_users}\n"
                          f"Количество начатых игр: {total_games}\n"
                          f"Количество выигранных игр: {won_games}")

# Обработка текстовых сообщений (угадывание числа)
@bot.message_handler(func=lambda message: True)
def handle_guess(message):
    chat_id = message.chat.id
    game_number = db.get_game_number(chat_id)

    if not game_number:
        bot.reply_to(message, "Игра не начата. Введи /game, чтобы начать!")
        return

    try:
        guess = int(message.text)
    except ValueError:
        bot.reply_to(message, "Пожалуйста, введи число!")
        return

    if guess < game_number:
        bot.reply_to(message, "Загаданное число больше.")
    elif guess > game_number:
        bot.reply_to(message, "Загаданное число меньше.")
    else:
        # Игра выиграна
        bot.reply_to(message, "Поздравляю! Ты угадал число. Введи /game, чтобы сыграть снова.")
        db.stop_game(chat_id, won=True)  # Помечаем игру как выигранную

# Запуск бота
bot.polling(none_stop=True)
