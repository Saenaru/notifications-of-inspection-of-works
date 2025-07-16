import os
import logging
import asyncio
import argparse
from dotenv import load_dotenv
import requests
from telegram import Bot

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

class DevmanNotifierBot:
    def __init__(self, chat_id):
        self.devman_api_key = os.getenv('DEVMAN_API_TOKEN')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id
        
        if not all([self.devman_api_key, self.telegram_token, self.chat_id]):
            raise ValueError("Не все необходимые переменные окружения установлены!")
        
        self.bot = Bot(token=self.telegram_token)
        self.last_timestamp = None

    async def check_reviews(self):
        headers = {"Authorization": f"Token {self.devman_api_key}"}
        params = {'timestamp': self.last_timestamp} if self.last_timestamp else {}
        
        try:
            response = requests.get(
                'https://dvmn.org/api/long_polling/',
                headers=headers,
                params=params,
                timeout=90
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ReadTimeout:
            logger.debug("Таймаут запроса, новых проверок нет")
            return {'status': 'timeout'}
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Ошибка соединения: {e}")
            await asyncio.sleep(5)
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return None

    @staticmethod
    def format_notification(attempt):
        lesson_title = attempt['lesson_title']
        result = ("К сожалению, в работе нашлись ошибки." 
                 if attempt['is_negative'] 
                 else "Преподавателю всё понравилось, можно приступать к следущему уроку!")
        
        return (
            f"Преподаватель проверил работу!\n\n"
            f"Урок: {lesson_title}\n"
            f"Результат: {result}"
        )

    async def send_notification(self, attempt):
        message = self.format_notification(attempt)
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")

    async def run(self):
        logger.info(f"Бот запущен для чата ID: {self.chat_id}. Начато отслеживание проверок...")
        
        while True:
            result = await self.check_reviews()
            
            if not result:
                continue
                
            if result.get('status') == 'found':
                for attempt in result['new_attempts']:
                    logger.info(f"Найдена новая проверка: {attempt['lesson_title']}")
                    await self.send_notification(attempt)
                self.last_timestamp = result['last_attempt_timestamp']
            
            await asyncio.sleep(3)

def get_chat_id():
    print("\nДля работы бота необходимо указать ваш Telegram Chat ID.")
    print("1. Отправьте любое сообщение боту в Telegram")
    print("2. Получить свой chat_id можно с помощью бота @userinfobot")
    print("3. Или найти его в URL при открытии чата с ботом в веб-версии Telegram")
    print("\nВведите ваш chat_id:")
    return input().strip()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Devman Notifier Bot')
    parser.add_argument('--chat-id', help='Telegram Chat ID для отправки уведомлений')
    args = parser.parse_args()

    chat_id = args.chat_id if args.chat_id else get_chat_id()
    
    notifier = DevmanNotifierBot(chat_id)
    
    try:
        asyncio.run(notifier.run())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        exit(1)