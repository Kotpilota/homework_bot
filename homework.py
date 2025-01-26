import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Dict, List

import requests
from dotenv import load_dotenv
from requests.exceptions import RequestException
from telebot import TeleBot
from telebot.apihelper import ApiTelegramException

from exceptions import APIResponseError, HomeworkStatusError

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

logger = logging.getLogger(__name__)


def check_tokens() -> List[str]:
    """
    Проверяет наличие всех переменных окружения.

    Returns:
        List[str]: Список отсутствующих переменных окружения.
    """
    missing_tokens = []
    if not PRACTICUM_TOKEN:
        missing_tokens.append('PRACTICUM_TOKEN')
    if not TELEGRAM_TOKEN:
        missing_tokens.append('TELEGRAM_TOKEN')
    if not TELEGRAM_CHAT_ID:
        missing_tokens.append('TELEGRAM_CHAT_ID')
    return missing_tokens


def send_message(bot: TeleBot, message: str) -> None:
    """
    Отправляет сообщение в Telegram.

    Args:
        bot (TeleBot): Объект Telegram-бота.
        message (str): Текст сообщения.
    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except (ApiTelegramException, RequestException) as error:
        logger.error(f'Ошибка отправки сообщения: {error}')
    else:
        logger.debug(f'Бот отправил сообщение: "{message}"')


def get_api_answer(timestamp: int) -> Dict:
    """
    Делает запрос к API Яндекс.Практикума.

    Args:
        timestamp (int): Временная метка.

    Returns:
        dict: Ответ API в формате словаря.
    """
    params = {'from_date': timestamp}
    logger.info(f'Начинаем запрос к API: {ENDPOINT} с параметрами {params}')
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise APIResponseError(
                f'Эндпоинт недоступен. Код: {response.status_code}'
            )
        return response.json()
    except RequestException as error:
        raise APIResponseError(f'Ошибка запроса к API: {error}')


def check_response(response: Dict) -> List[Dict]:
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


def parse_status(homework: Dict) -> str:
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


def main() -> None:
    """Основной цикл работы бота."""
    missing_tokens = check_tokens()
    if missing_tokens:
        for token in missing_tokens:
            logger.critical(f'Отсутствует переменная окружения: {token}')
        sys.exit(
            'Программа остановлена из-за отсутствия переменных окружения.'
        )

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_error = None
    previous_status = None

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)

            if homeworks:
                last_homework = homeworks[0]
                message = parse_status(last_homework)

                if message != previous_status:
                    send_message(bot, message)
                    previous_status = message

                timestamp = response.get('current_date', timestamp)
            else:
                message = 'Новых статусов нет.'
                if message != previous_status:
                    send_message(bot, message)
                    previous_status = message

        except Exception as error:
            logger.error(f'Ошибка в работе программы: {error}')
            if previous_error != error:
                send_message(bot, f'Ошибка в работе программы: {error}')
                previous_error = error
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    main()
