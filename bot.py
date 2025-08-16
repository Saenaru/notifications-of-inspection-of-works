import os
import logging
import time
from dotenv import load_dotenv
import requests
from telegram import Bot
from telegram.error import TelegramError
import traceback

logger = logging.getLogger(__name__)

def setup_logging(log_bot, log_chat_id):
    """Настройка логгера для отправки сообщений в Telegram"""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    class TelegramHandler(logging.Handler):
        def emit(self, record):
            try:
                log_bot.send_message(
                    chat_id=log_chat_id,
                    text=self.format(record)
                )
            except TelegramError as e:
                print(f"Ошибка отправки лога: {e}")
    
    telegram_handler = TelegramHandler()
    telegram_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(telegram_handler)

def check_for_new_reviews(api_key, last_ts=None):
    """Проверка новых ревью на Devman"""
    response = requests.get(
        'https://dvmn.org/api/long_polling/',
        headers={'Authorization': f"Token {api_key}"},
        params={'timestamp': last_ts} if last_ts else {},
        timeout=90
    )
    response.raise_for_status()
    return response.json()

def format_review_message(attempt):
    """Форматирование сообщения о проверке"""
    status = "Есть ошибки" if attempt['is_negative'] else "Принято"
    return (
        f"<b>Проверена работа:</b> {attempt['lesson_title']}\n"
        f"<b>Результат:</b> {status}\n"
    )

def main():
    try:
        load_dotenv()
        
        notification_bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
        log_bot = Bot(token=os.getenv('LOG_BOT_TOKEN'))
        chat_id = os.getenv('CHAT_ID')
        
        setup_logging(log_bot, chat_id)
        logger.info("Бот запущен. Ожидание проверок...")
        
        last_ts = None
        while True:
            try:
                result = check_for_new_reviews(os.getenv('DEVMAN_TOKEN'), last_ts)
                
                if result.get('status') == 'found':
                    for attempt in result['new_attempts']:
                        notification_bot.send_message(
                            chat_id=chat_id,
                            text=format_review_message(attempt),
                            parse_mode='HTML'
                        )
                        logger.info(f"Отправлено уведомление: {attempt['lesson_title']}")
                    
                    last_ts = result['last_attempt_timestamp']
                    
            except requests.exceptions.ReadTimeout:
                continue
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка API Devman: {e}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}")
                time.sleep(1)
                
    except Exception as e:
        logger.critical(f"Критическая ошибка:\n{traceback.format_exc()}")
        raise

if __name__ == '__main__':
    main()