import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters


async def start(update: Update, context):
    """Обработчик команды /start."""
    await update.message.reply_text('Здравствуйте')


async def echo(update: Update, context):
    """Обработчик любого текстового сообщения. Повторяет текст за пользователем."""
    await update.message.reply_text(update.message.text)


def main():
    """Точка входа. Запускает бота."""
    # Загружаем переменные из файла .env
    load_dotenv()
    
    # Получаем токен из переменной окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("Ошибка: токен TELEGRAM_BOT_TOKEN не найден в файле .env")

    # Создаем объект Application (замена старому Updater)
    application = Application.builder().token(token).build()
    
    # Регистрируем обработчики (хэндлеры)
    # Если пришла команда /start -> вызываем асинхронную функцию start
    application.add_handler(CommandHandler("start", start))
    
    # Если пришел просто текст (и это не команда) -> вызываем асинхронную функцию echo
    # filters.TEXT & ~filters.COMMAND означает: "Только текст, НО не команды"
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Запускаем бесконечный опрос серверов Telegram
    # run_polling() сам блокирует выполнение скрипта
    application.run_polling()


if __name__ == '__main__':
    main()