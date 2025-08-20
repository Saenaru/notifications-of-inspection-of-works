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
    try:
        load_dotenv()
        
        log_bot_token = os.environ['LOG_BOT_TOKEN']
        telegram_token = os.environ['TELEGRAM_TOKEN']
        chat_id = os.environ['CHAT_ID']
        devman_token = os.environ['DEVMAN_TOKEN']
        
        log_bot = Bot(token=log_bot_token)
        notification_bot = Bot(token=telegram_token)
        
        setup_logging(log_bot, chat_id)
        logger.info("Бот запущен. Ожидание проверок...")
        
        last_ts = None
        while True:
            try:
                result = check_for_new_reviews(devman_token, last_ts)
            except requests.exceptions.ReadTimeout:
                continue
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка API Devman: {e}")
                time.sleep(5)
                continue
            except Exception as e:
                logger.error(f"Неожиданная ошибка при проверке ревью: {e}")
                time.sleep(1)
                continue
            
            try:
                if result.get('status') == 'found':
                    for attempt in result['new_attempts']:
                        notification_bot.send_message(
                            chat_id=chat_id,
                            text=format_review_message(attempt),
                            parse_mode='HTML'
                        )
                        logger.info(f"Отправлено уведомление: {attempt['lesson_title']}")
                    
                    last_ts = result['last_attempt_timestamp']
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомлений: {e}")
                time.sleep(1)
                
    except KeyError as e:
        error_msg = f"Отсутствует обязательная переменная окружения: {e}"
        print(error_msg)
        raise
    except Exception as e:
        error_msg = f"Критическая ошибка:\n{traceback.format_exc()}"
        try:
            log_bot_token = os.environ.get('LOG_BOT_TOKEN')
            chat_id = os.environ.get('CHAT_ID')
            if log_bot_token and chat_id:
                log_bot = Bot(token=log_bot_token)
                log_bot.send_message(
                    chat_id=chat_id,
                    text=error_msg,
                    parse_mode='HTML'
                )
        except Exception as send_error:
            print(f"Не удалось отправить ошибку: {send_error}")
        raise

if __name__ == '__main__':
    main()