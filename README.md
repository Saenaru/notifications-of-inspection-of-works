# Devman Notifier Bot

Telegram-бот для отслеживания проверок домашних заданий на платформе Devman (dvmn.org). Бот уведомляет о результатах проверки работ преподавателем.

## Возможности

- Автоматическая проверка статуса проверки домашних заданий
- Мгновенные уведомления в Telegram:
  - Когда работа проверена
  - Результат проверки (принято/есть ошибки)
  - Название урока

## Установка и настройка

### Требования
- Python 3.8+
- Аккаунт на [dvmn.org](https://dvmn.org/)
- Telegram-бот (получить у [@BotFather](https://t.me/BotFather))

### 1. Клонирование репозитория
```bash
git clone https://github.com/ваш-username/devman-notifier-bot.git
cd devman-notifier-bot
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка окружения
Создайте файл .env в корне проекта и добавьте:

```bash
DEVMAN_TOKEN=ваш_api_ключ_devman
TELEGRAM_TOKEN=ваш_токен_telegram_bot
CHAT_ID=ваш_telegram_ID
```

### 4. Получение Chat ID
- Отправьте любое сообщение вашему боту в Telegram
- Получите свой chat_id одним из способов:
  - Через бота @userinfobot
  - Из URL в веб-версии Telegram (например: https://web.telegram.org/#/im?p=u123456789_ → chat_id = 123456789)

## Запуск бота

```bash
python bot.py
```

## Цели проекта

Код написан в учебных целях — для курса по Python и веб-разработке на сайте [Devman](https://dvmn.org).