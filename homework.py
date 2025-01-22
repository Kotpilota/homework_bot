import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot

from exceptions import APIResponseError, HomeworkStatusError, MissingTokenError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def check_tokens():
    """
    Проверяет наличие всех переменных окружения.

    Returns:
        bool: True, если все токены присутствуют.
    """
    tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    if not all(tokens):
        raise MissingTokenError(
            'Отсутствуют обязательные переменные окружения.'
        )
    return True


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram.

    Args:
        bot (TeleBot): Объект Telegram-бота.
        message (str): Текст сообщения.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Бот отправил сообщение: "{message}"')
    except Exception as error:
        logger.error(f'Ошибка отправки сообщения: {error}')


def get_api_answer(timestamp):
    """
    Делает запрос к API Яндекс.Практикума.

    Args:
        timestamp (int): Временная метка.

    Returns:
        dict: Ответ API в формате словаря.
    """
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise APIResponseError(
                f'Эндпоинт недоступен. Код: {response.status_code}'
            )
        return response.json()
    except requests.RequestException as error:
        raise APIResponseError(f'Ошибка запроса к API: {error}')


def check_response(response):
    """
    Проверяет корректность ответа API.

    Args:
        response (dict): Ответ API.

    Returns:
        list: Список домашних работ.
    """
    if not isinstance(response, dict):
        raise TypeError('Ответ API должен быть словарём.')
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError('Отсутствуют необходимые ключи в ответе API.')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Ключ homeworks должен содержать список.')
    return response['homeworks']


def parse_status(homework):
    """
    Извлекает статус домашней работы.

    Args:
        homework (dict): Данные о работе.

    Returns:
        str: Сообщение о статусе работы.
    """
    if 'homework_name' not in homework or 'status' not in homework:
        raise KeyError('Нет ключей homework_name или status.')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise HomeworkStatusError(f'Неизвестный статус: {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основной цикл работы бота."""
    try:
        check_tokens()
    except MissingTokenError as e:
        logger.critical(e)
        sys.exit('Программа остановлена.')

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_error = None

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                for homework in homeworks:
                    message = parse_status(homework)
                    send_message(bot, message)
            else:
                logger.debug('Новых статусов нет.')
            timestamp = response.get('current_date', timestamp)
        except Exception as error:
            logger.error(f'Ошибка в работе программы: {error}')
            if previous_error != str(error):
                send_message(bot, f'Ошибка в работе программы: {error}')
                previous_error = str(error)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
