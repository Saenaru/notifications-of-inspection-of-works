import os
import logging
import time
from dotenv import load_dotenv
import requests
from telegram import Bot
from telegram.error import TelegramError


logger = logging.getLogger(__name__)


class TelegramLogsHandler(logging.Handler):
    def __init__(self, bot, chat_id):
        super().__init__()
        self.bot = bot
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        try:
            self.bot.send_message(chat_id=self.chat_id, text=log_entry)
        except TelegramError as e:
            print(f"Ошибка при отправке лога в Telegram: {e}")


def check_for_new_reviews(api_key, last_ts=None):
    response = requests.get(
        'https://dvmn.org/api/long_polling/',
        headers={'Authorization': f"Token {api_key}"},
        params={'timestamp': last_ts} if last_ts else {},
        timeout=90
    )
    response.raise_for_status()
    return response.json()


def main():
    load_dotenv()
    devman_token = os.getenv('DEVMAN_TOKEN')
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')

    if not devman_token:
        raise ValueError("Переменная DEVMAN_TOKEN не установлена")
    if not telegram_token:
        raise ValueError("Переменная TELEGRAM_TOKEN не установлена")
    if not chat_id:
        raise ValueError("Переменная CHAT_ID не установлена")

    bot = Bot(token=telegram_token)
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    telegram_handler = TelegramLogsHandler(bot, chat_id)
    telegram_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(telegram_handler)
    
    logger.info(f"Бот запущен для чата {chat_id}")
    last_ts = None
    while True:
        try:
            result = check_for_new_reviews(devman_token, last_ts)
            if result and result.get('status') == 'found':
                for attempt in result['new_attempts']:
                    lesson = attempt['lesson_title']
                    result_msg = (
                        "К сожалению, в работе нашлись ошибки."
                        if attempt['is_negative']
                        else "Преподавателю всё понравилось, "
                             "можно приступать к следующему уроку!"
                    )
                    msg = (
                        f"Преподаватель проверил работу!\n"
                        f"Урок: {lesson}\n"
                        f"Результат: {result_msg}"
                    )
                    try:
                        bot.send_message(
                            chat_id=chat_id,
                            text=msg,
                            parse_mode='HTML'
                        )
                        logger.info(f"Уведомление отправлено: {lesson}")
                    except TelegramError as e:
                        logger.error(f"Ошибка Telegram: {e}")
                last_ts = result['last_attempt_timestamp']
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к API Devman: {e}")
            time.sleep(5)
            continue
        time.sleep(1)


if __name__ == '__main__':
    main()