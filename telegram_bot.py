import os
import random
import re
import redis
from enum import Enum
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters,
    ConversationHandler
)
from main import load_all_questions


class QuizState(Enum):
    """Состояния диалога бота."""
    CHOOSING = 1
    ANSWERING = 2


QUIZ_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("Новый вопрос"), KeyboardButton("Сдаться")],
        [KeyboardButton("Мой счет")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)


def extract_main_answer(text):
    """Извлекает основную часть ответа для мягкой проверки."""
    if not text:
        return ""
    
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)
    text = re.sub(r'\([^)]*\)', '', text)
    if '.' in text:
        text = text.split('.')[0]
    
    return ' '.join(text.lower().split())


async def start(update: Update, context):
    await update.message.reply_text(
        'Здравствуйте! Выберите действие:',
        reply_markup=QUIZ_KEYBOARD
    )
    return QuizState.CHOOSING


async def handle_new_question_request(update: Update, context):
    user_id = update.effective_user.id
    questions = context.bot_data.get('questions', {})
    redis_client = context.bot_data.get('redis_client')
    
    if questions:
        random_question = random.choice(list(questions.keys()))
        correct_answer = questions[random_question]
        
        redis_client.hset(
            name=f"user_{user_id}", 
            mapping={"question": random_question, "answer": correct_answer}
        )
        
        await update.message.reply_text(random_question, reply_markup=QUIZ_KEYBOARD)
        return QuizState.ANSWERING
    else:
        await update.message.reply_text("Вопросы не загружены!", reply_markup=QUIZ_KEYBOARD)
        return QuizState.CHOOSING


async def handle_solution_attempt(update: Update, context):
    user_text = update.message.text.strip()
    user_id = update.effective_user.id
    redis_client = context.bot_data.get('redis_client')
    
    stored_data = redis_client.hgetall(f"user_{user_id}")
    if not stored_data:
        await update.message.reply_text("Сначала нажмите кнопку 'Новый вопрос'!", reply_markup=QUIZ_KEYBOARD)
        return QuizState.CHOOSING

    correct_answer = stored_data["answer"]
    main_answer = extract_main_answer(correct_answer)
    normalized_user = extract_main_answer(user_text)
    
    if normalized_user == main_answer:
        await update.message.reply_text(
            "Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»", 
            reply_markup=QUIZ_KEYBOARD
        )
        return QuizState.CHOOSING
    else:
        await update.message.reply_text(
            "Неправильно… Попробуешь ещё раз?", 
            reply_markup=QUIZ_KEYBOARD
        )
        return QuizState.ANSWERING


async def handle_surrender(update: Update, context):
    """Обработчик нажатия кнопки 'Сдаться'."""
    user_id = update.effective_user.id
    redis_client = context.bot_data.get('redis_client')
    questions = context.bot_data.get('questions', {})
    
    stored_data = redis_client.hgetall(f"user_{user_id}")
    
    if stored_data and "answer" in stored_data:
        correct_answer = extract_main_answer(stored_data["answer"])
        await update.message.reply_text(
            f"Правильный ответ: {correct_answer}",
            reply_markup=QUIZ_KEYBOARD
        )
    else:
        await update.message.reply_text(
            "Вы ещё не начали вопрос!",
            reply_markup=QUIZ_KEYBOARD
        )

    if questions:
        random_question = random.choice(list(questions.keys()))
        correct_answer = questions[random_question]
        
        redis_client.hset(
            name=f"user_{user_id}", 
            mapping={
                "question": random_question,
                "answer": correct_answer
            }
        )
        
        await update.message.reply_text(
            random_question,
            reply_markup=QUIZ_KEYBOARD
        )
        return QuizState.ANSWERING
        
    return QuizState.CHOOSING


async def handle_score(update: Update, context):
    await update.message.reply_text(
        "Функция подсчета очков будет добавлена позже.",
        reply_markup=QUIZ_KEYBOARD
    )
    return QuizState.CHOOSING


async def cancel(update: Update, context):
    await update.message.reply_text("До свидания!", reply_markup=QUIZ_KEYBOARD)
    return ConversationHandler.END


async def post_init(application: Application):
    questions = load_all_questions()
    application.bot_data['questions'] = questions
    print(f"Загружено вопросов: {len(questions)}")
    
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT')),
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True
    )
    redis_client.ping()
    print("Успешное подключение к Redis!")
    application.bot_data['redis_client'] = redis_client


def main():
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("Ошибка: токен TELEGRAM_BOT_TOKEN не найден в файле .env")

    application = Application.builder().token(token).build()
    application.post_init = post_init
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            QuizState.CHOOSING: [
                MessageHandler(filters.Regex("^Новый вопрос$"), handle_new_question_request),
                MessageHandler(filters.Regex("^Сдаться$"), handle_surrender),
                MessageHandler(filters.Regex("^Мой счет$"), handle_score),
            ],
            QuizState.ANSWERING: [
                MessageHandler(filters.Regex("^Сдаться$"), handle_surrender),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_solution_attempt),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="quiz_conversation",
        persistent=False
    )
    
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()