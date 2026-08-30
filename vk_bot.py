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


def get_quiz_keyboard():
    """Создаёт и возвращает клавиатуру для викторины."""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def extract_main_answer(text):
    """Извлекает основную часть ответа для мягкой проверки."""
    if not text:
        return ""
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)
    text = re.sub(r'\([^)]*\)', '', text)
    if '.' in text:
        text = text.split('.')[0]
    return ' '.join(text.lower().split())


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
        if event.type == VkBotEventType.MESSAGE_NEW and event.from_user:
            user_text = event.obj.message['text'].strip()
            user_id = event.obj.message['from_id']
            peer_id = event.obj.message['peer_id']
            
            print(f"Получено от {user_id}: '{user_text}'")
                        
            if user_text == "Новый вопрос":
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
                    
                    vk.messages.send(
                        peer_id=peer_id,
                        message=random_question,
                        keyboard=get_quiz_keyboard(),
                        random_id=get_random_id()
                    )
                else:
                    vk.messages.send(
                        peer_id=peer_id,
                        message="Вопросы не загружены!",
                        keyboard=get_quiz_keyboard(),
                        random_id=get_random_id()
                    )
            
            elif user_text == "Сдаться":
                stored_data = redis_client.hgetall(f"user_{user_id}")
                if stored_data and "answer" in stored_data:
                    correct_answer = extract_main_answer(stored_data["answer"])
                    vk.messages.send(
                        peer_id=peer_id,
                        message=f"Правильный ответ: {correct_answer}",
                        keyboard=get_quiz_keyboard(),
                        random_id=get_random_id()
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
                        vk.messages.send(
                            peer_id=peer_id,
                            message=random_question,
                            keyboard=get_quiz_keyboard(),
                            random_id=get_random_id()
                        )
                else:
                    vk.messages.send(
                        peer_id=peer_id,
                        message="Вы ещё не начали вопрос!",
                        keyboard=get_quiz_keyboard(),
                        random_id=get_random_id()
                    )
            
            elif user_text == "Мой счет":
                correct = int(redis_client.hget(f"user_{user_id}", "correct_answers") or 0)
                wrong = int(redis_client.hget(f"user_{user_id}", "wrong_answers") or 0)
                vk.messages.send(
                    peer_id=peer_id,
                    message=f"Ваш счет:\nПравильных ответов: {correct}\nНеправильных ответов: {wrong}",
                    keyboard=get_quiz_keyboard(),
                    random_id=get_random_id()
                )
            
            else:
                stored_data = redis_client.hgetall(f"user_{user_id}")
                if not stored_data or "answer" not in stored_data:
                    vk.messages.send(
                        peer_id=peer_id,
                        message="Сначала нажмите кнопку 'Новый вопрос'!",
                        keyboard=get_quiz_keyboard(),
                        random_id=get_random_id()
                    )
                else:
                    correct_answer = stored_data["answer"]
                    main_answer = extract_main_answer(correct_answer)
                    normalized_user = extract_main_answer(user_text)
                    
                    if normalized_user == main_answer:
                        redis_client.hincrby(f"user_{user_id}", "correct_answers", 1)
                        redis_client.hdel(f"user_{user_id}", "question", "answer")
                        vk.messages.send(
                            peer_id=peer_id,
                            message="Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»",
                            keyboard=get_quiz_keyboard(),
                            random_id=get_random_id()
                        )
                    else:
                        redis_client.hincrby(f"user_{user_id}", "wrong_answers", 1)
                        vk.messages.send(
                            peer_id=peer_id,
                            message="Неправильно… Попробуешь ещё раз?",
                            keyboard=get_quiz_keyboard(),
                            random_id=get_random_id()
                        )


if __name__ == '__main__':
    main()