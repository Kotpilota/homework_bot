class MissingTokenError(Exception):
    """Отсутствуют необходимые переменные окружения."""


class APIResponseError(Exception):
    """Произошла ошибка при запросе к API."""


class HomeworkStatusError(Exception):
    """Статус домашней работы неизвестен."""
