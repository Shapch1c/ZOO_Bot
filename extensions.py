import telebot
from telebot import types
import config
import animals
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

bot = telebot.TeleBot(config.TOKEN)

questions = [
    {
        "question": "Какое место ты предпочитаешь для жизни?",
        "options": ["Лес", "Пустыня", "Горы", "Водоем"],
        "points": {"Лес": 2, "Пустыня": 1, "Горы": 3, "Водоем": 2}
    },
    {
        "question": "Какую еду ты предпочитаешь?",
        "options": ["Мясо", "Фрукты", "Травы", "Рыба"],
        "points": {"Мясо": 3, "Фрукты": 1, "Травы": 2, "Рыба": 2}
    }
]

user_answers = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_answers[message.chat.id] = []
    logging.info(f"User {message.chat.id} started the quiz.")
    bot.send_message(message.chat.id, "Привет! Пройди викторину, чтобы узнать своё тотемное животное!")
    ask_question(message)

def ask_question(message):
    answers = user_answers.get(message.chat.id, [])
    question_index = len(answers)
    if question_index >= len(questions):
        show_results(message)
        return

    question = questions[question_index]
    options = question['options']

    if question_index == 1:
        place = answers[0]
        if place == "Пустыня":
            options = ["Мясо", "Травы"]
        elif place == "Водоем":
            options = ["Рыба"]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for opt in options:
        markup.add(opt)

    logging.info(f"User {message.chat.id} is being asked: {question['question']} Options: {options}")
    bot.send_message(message.chat.id, question['question'], reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Давай ещё раз!")
def restart_quiz(message):
    user_answers[message.chat.id] = []
    logging.info(f"User {message.chat.id} restarted the quiz.")
    ask_question(message)

@bot.message_handler(func=lambda message: True)
def handle_answer(message):
    chat_id = message.chat.id
    if chat_id not in user_answers:
        user_answers[chat_id] = []

    answer = message.text
    question_index = len(user_answers[chat_id])

    if question_index >= len(questions):
        ask_question(message)
        return

    question = questions[question_index]
    if answer not in question['options']:
        bot.send_message(chat_id, "Пожалуйста, выбери один из предложенных вариантов.")
        logging.warning(f"User {chat_id} sent invalid answer: {answer}")
        return

    user_answers[chat_id].append(answer)
    logging.info(f"User {chat_id} answered question {question_index}: {answer}")
    ask_question(message)

def show_results(message):
    answers = user_answers.get(message.chat.id, [])
    if len(answers) < 2:
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте ещё раз.")
        logging.error(f"User {message.chat.id} has insufficient answers: {answers}")
        return

    place, food = answers[:2]
    animal = get_animal_by_place_and_food(place, food)

    logging.info(f"User {message.chat.id} got result: {animal['name']}")
    bot.send_message(message.chat.id, f"Твоё тотемное животное — {animal['name']}!")
    try:
        bot.send_photo(message.chat.id, animal['image_url'])
    except Exception as e:
        logging.error(f"Failed to send photo to {message.chat.id}: {e}")
        bot.send_message(message.chat.id, "(Не удалось загрузить изображение)")

    bot.send_message(message.chat.id, animal['description'])

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Давай ещё раз!")

    bot.send_message(message.chat.id, "Хочешь пройти викторину снова?", reply_markup=markup)
    bot.send_message(message.chat.id, "Следите за нами в Instagram и VK: @zoototems")
    bot.send_message(message.chat.id, "Если у вас есть вопросы или отзывы, напишите нам: support@example.com")
    bot.send_message(message.chat.id, "Все ваши данные анонимны и не сохраняются. Спасибо за участие!")

def get_animal_by_place_and_food(place, food):
    return animals.animals.get(place, {}).get(food, {
        "name": "Неизвестно",
        "image_url": "",
        "description": "Не удалось определить тотемное животное."
    })

if __name__ == '__main__':
    logging.info("Bot started polling.")
    print("Бот запущен и ожидает подключения...")
    bot.polling(none_stop=True)
