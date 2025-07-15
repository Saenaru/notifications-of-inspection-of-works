import requests
import time

headers = {
    "Authorization": "7bc6cd383b1d3a41c132a40b11771802bec30009"
}

def check_new_attempts(last_timestamp=None):
    params = {}
    if last_timestamp:
        params = {'timestamp': last_timestamp}
    
    response = requests.get(
        "https://dvmn.org/api/long_polling/",
        headers=headers,
        params=params,
        timeout=90
    )
    response.raise_for_status()
    return response.json()

last_timestamp = None
while True:
    try:
        result = check_new_attempts(last_timestamp)
        print("Получен ответ:", result)
        
        if result['status'] == 'found':
            for attempt in result['new_attempts']:
                print(f"Новая проверка: {attempt['lesson_title']}")
                print(f"Результат: {'Неудача' if attempt['is_negative'] else 'Успех'}")
            last_timestamp = result['last_attempt_timestamp']
        elif result['status'] == 'timeout':
            print("Новых проверок нет, продолжаем опрос...")
            
    except requests.exceptions.ReadTimeout:
        print("Таймаут соединения, повторяем запрос...")
    except requests.exceptions.ConnectionError:
        print("Ошибка соединения, пробуем через 5 секунд...")
        time.sleep(5)
    except Exception as err:
        print(f"Неизвестная ошибка: {err}")
        time.sleep(5)