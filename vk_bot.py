import os
import random
import re
import redis
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from dotenv import load_dotenv
from main import load_all_questions
from answer_checker import extract_main_answer


def get_quiz_keyboard():
    """Создаёт и возвращает клавиатуру для викторины."""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def send_message(vk, peer_id, message):
    """Отправляет сообщение с клавиатурой."""
    vk.messages.send(
        peer_id=peer_id,
        message=message,
        keyboard=get_quiz_keyboard(),
        random_id=get_random_id()
    )


def handle_new_question(vk, peer_id, questions, redis_client, user_id):
    """Обработка кнопки 'Новый вопрос'."""
    if not questions:
        send_message(vk, peer_id, "Вопросы не загружены!")
        return
    
    random_question = random.choice(list(questions.keys()))
    correct_answer = questions[random_question]
    
    redis_client.hset(
        name=f"vk_user_{user_id}",
        mapping={
            "question": random_question,
            "answer": correct_answer
        }
    )
    
    send_message(vk, peer_id, random_question)


def handle_surrender(vk, peer_id, questions, redis_client, user_id):
    """Обработка кнопки 'Сдаться'."""
    stored_data = redis_client.hgetall(f"vk_user_{user_id}")
    
    if not stored_data or "answer" not in stored_data:
        send_message(vk, peer_id, "Вы ещё не начали вопрос!")
        return
    
    correct_answer = extract_main_answer(stored_data["answer"])
    send_message(vk, peer_id, f"Правильный ответ: {correct_answer}")
    
    if not questions:
        return
    
    random_question = random.choice(list(questions.keys()))
    correct_answer = questions[random_question]
    
    redis_client.hset(
        name=f"vk_user_{user_id}",
        mapping={
            "question": random_question,
            "answer": correct_answer
        }
    )
    
    send_message(vk, peer_id, random_question)


def handle_score(vk, peer_id, redis_client, user_id):
    """Обработка кнопки 'Мой счет'."""
    correct = int(redis_client.hget(f"vk_user_{user_id}", "correct_answers") or 0)
    wrong = int(redis_client.hget(f"vk_user_{user_id}", "wrong_answers") or 0)
    
    message = f"Ваш счет:\nПравильных ответов: {correct}\nНеправильных ответов: {wrong}"
    send_message(vk, peer_id, message)


def handle_answer(vk, peer_id, user_text, redis_client, user_id):
    """Обработка текстового ответа на вопрос."""
    stored_data = redis_client.hgetall(f"vk_user_{user_id}")
    
    if not stored_data or "answer" not in stored_data:
        send_message(vk, peer_id, "Сначала нажмите кнопку 'Новый вопрос'!")
        return
    
    correct_answer = stored_data["answer"]
    main_answer = extract_main_answer(correct_answer)
    normalized_user = extract_main_answer(user_text)
    
    if normalized_user == main_answer:
        redis_client.hincrby(f"vk_user_{user_id}", "correct_answers", 1)
        redis_client.hdel(f"vk_user_{user_id}", "question", "answer")
        send_message(vk, peer_id, "Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»")
    else:
        redis_client.hincrby(f"vk_user_{user_id}", "wrong_answers", 1)
        send_message(vk, peer_id, "Неправильно… Попробуешь ещё раз?")            


def main():
    """Точка входа. Запускает VK-бота с полным функционалом викторины."""
    load_dotenv()
    
    group_token = os.getenv('VK_GROUP_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')
    
    if not group_token or not group_id:
        raise ValueError("Ошибка: VK_GROUP_TOKEN или VK_GROUP_ID не найдены в .env")

    questions = load_all_questions()
    print(f"Загружено вопросов: {len(questions)}")
    
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT')),
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True
    )
    redis_client.ping()
    print("Успешное подключение к Redis!")

    vk_session = vk_api.VkApi(token=group_token)
    vk = vk_session.get_api()
    
    longpoll = VkBotLongPoll(vk_session, group_id=int(group_id))
    print("VK бот запущен и слушает события...")

    for event in longpoll.listen():
        if event.type != VkBotEventType.MESSAGE_NEW or not event.from_user:
            continue

        user_text = event.obj.message['text'].strip()
        user_id = event.obj.message['from_id']
        peer_id = event.obj.message['peer_id']
            
        print(f"Получено от {user_id}: '{user_text}'")

        if user_text == "Новый вопрос":
            handle_new_question(vk, peer_id, questions, redis_client, user_id)
        elif user_text == "Сдаться":
            handle_surrender(vk, peer_id, questions, redis_client, user_id)
        elif user_text == "Мой счет":
            handle_score(vk, peer_id, redis_client, user_id)
        else:
            handle_answer(vk, peer_id, user_text, redis_client, user_id)
                        

if __name__ == '__main__':
    main()