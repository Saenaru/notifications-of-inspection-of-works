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
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    class TelegramHandler(logging.Handler):
        def emit(self, record):
            try:
                log_bot.send_message(
                    chat_id=log_chat_id,
                    text=self.format(record),
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Ошибка отправки лога: {e}")
    
    telegram_handler = TelegramHandler()
    telegram_handler.setFormatter(logging.Formatter(
        '<b>%(levelname)s</b> - %(name)s\n%(asctime)s\n%(message)s'
    ))
    logging.getLogger().addHandler(telegram_handler)

def main():
    log_bot = None
    try:
        load_dotenv()
        
        log_bot = Bot(token=os.getenv('LOG_BOT_TOKEN'))
        notification_bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
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
        error_msg = f"Критическая ошибка:\n{traceback.format_exc()}"
        try:
            if log_bot:
                log_bot.send_message(
                    chat_id=os.getenv('CHAT_ID'),
                    text=error_msg,
                    parse_mode='HTML'
                )
        except Exception as send_error:
            print(f"Не удалось отправить ошибку: {send_error}")
        raise

if __name__ == '__main__':
    main()