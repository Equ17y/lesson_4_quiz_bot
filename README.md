# Бот-викторина для Исторического музея

Чат-бот для проведения викторины по истории. Поддерживает Telegram и ВКонтакте. 
Бот задает каверзные вопросы, проверяет ответы, ведет счет и позволяет сдаться, если вопрос слишком сложный.

## Ссылки на ботов
- **Telegram:** [Ссылка на твоего бота в Telegram](https://t.me/ТВОЙ_НИК_БОТА)
- **ВКонтакте:** [Ссылка на сообщество в ВК](https://vk.com/ТВОЕ_СООБЩЕСТВО)

## Как запустить локально

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Equ17y/lesson_4_quiz_bot.git
   cd lesson_4_quiz_bot
   ```

2. Создайте виртуальное окружение и установите зависимости:
    ```bash
    python -m venv venv
    # Для Windows:
    venv\Scripts\activate
    # Для macOS/Linux:
    source venv/bin/activate
    
    pip install -r requirements.txt
    ```   

3. оздайте файл .env и заполните его переменными (токены ботов, Redis):
    ```env
    TELEGRAM_BOT_TOKEN=ваш_токен
    VK_GROUP_TOKEN=ваш_токен
    VK_GROUP_ID=ваш_id
    REDIS_HOST=ваш_хост
    REDIS_PORT=ваш_порт
    REDIS_PASSWORD=ваш_пароль
    ```

4. Запустите ботов:
    ```bash
    python telegram_bot.py
    python vk_bot.py
    ```    