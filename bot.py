import os
import logging
import time
from dotenv import load_dotenv
import requests
from telegram import Bot
from telegram.error import TelegramError


logger = logging.getLogger(__name__)


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
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    try:
        devman_token = os.getenv('DEVMAN_TOKEN')
        telegram_token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('CHAT_ID')

        if not devman_token:
            logger.critical("Отсутствует переменная окружения: DEVMAN_TOKEN")
            raise ValueError("Переменная DEVMAN_TOKEN не установлена")
        if not telegram_token:
            logger.critical("Отсутствует переменная окружения: TELEGRAM_TOKEN")
            raise ValueError("Переменная TELEGRAM_TOKEN не установлена")
        if not chat_id:
            logger.critical("Отсутствует переменная окружения: CHAT_ID")
            raise ValueError("Переменная CHAT_ID не установлена")

        bot = Bot(token=telegram_token)
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
    except KeyboardInterrupt:
        logger.info("Бот остановлен по запросу пользователя")
    except Exception as e:
        logger.critical(f"Критическая ошибка в работе бота: {e}")
    finally:
        logger.info("Работа бота завершена")


if __name__ == '__main__':
    main()
