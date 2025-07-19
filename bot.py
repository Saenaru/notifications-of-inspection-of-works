import os
import logging
import time
from dotenv import load_dotenv
import requests
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

def send_telegram_message(bot, chat_id, text):
    try:
        # Синхронный вызов в v13
        bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='HTML'
        )
        logger.info(f"Сообщение отправлено: {text[:50]}...")
        return True
    except TelegramError as e:
        logger.error(f"Ошибка Telegram: {e}")
        return False

def notify(bot, chat_id, attempt):
    lesson = attempt['lesson_title']
    msg = (f"Проверка работы:\nУрок: {lesson}\n"
           f"Результат: {'К сожалению, в работе нашлись ошибки.' if attempt['is_negative'] else 'Преподавателю всё понравилось, можно приступать к следующему уроку!'}")
    
    if send_telegram_message(bot, chat_id, msg):
        logger.info(f"Уведомление обработано: {lesson}")
    else:
        logger.warning(f"Не удалось отправить уведомление для урока: {lesson}")

def poll_reviews(api_key, last_ts=None):
    try:
        response = requests.get(
            'https://dvmn.org/api/long_polling/',
            headers={'Authorization': f"Token {api_key}"},
            params={'timestamp': last_ts} if last_ts else {},
            timeout=90
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ReadTimeout:
        return {'status': 'timeout'}
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к API Devman: {e}")
        time.sleep(5)
        return None

def main():
    load_dotenv()
    setup_logging()
    
    required_vars = ['DEVMAN_TOKEN', 'TELEGRAM_TOKEN', 'CHAT_ID']
    if missing := [var for var in required_vars if not os.getenv(var)]:
        logger.critical(f"Отсутствуют переменные окружения: {missing}")
        return

    try:
        # Инициализация синхронного бота v13
        bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
        chat_id = os.getenv('CHAT_ID')
        last_ts = None

        logger.info(f"Бот запущен для чата {chat_id}")
        
        while True:
            result = poll_reviews(os.getenv('DEVMAN_TOKEN'), last_ts)
            
            if result and result.get('status') == 'found':
                for attempt in result['new_attempts']:
                    logger.info(f"Найдена новая проверка: {attempt['lesson_title']}")
                    notify(bot, chat_id, attempt)
                last_ts = result['last_attempt_timestamp']
            
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Бот остановлен по запросу пользователя")
    except Exception as e:
        logger.critical(f"Критическая ошибка в работе бота: {e}")
    finally:
        logger.info("Работа бота завершена")

if __name__ == '__main__':
    main()