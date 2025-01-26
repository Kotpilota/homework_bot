# Телеграм-бот для получения статусов домашних заданий с Яндекс.Практикума

Этот проект представляет собой Telegram-бота, который автоматически отслеживает статус ваших домашних заданий на Яндекс.Практикуме и отправляет уведомления о смене статуса.

## Установка

Для начала работы с проектом выполните следующие шаги:

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/Kotpilota/homework_bot.git
cd homework_bot
```

### 2. Создайте виртуальное окружение и активируйте его
```bash
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

### 3. Установите зависимости
```bash
pip install -r requirements.txt
```

### 4. Создайте файл .env
```bash
cp .env.example .env
```

### 5. Заполните переменные окружения в файле .env

* PRACTICUM_TOKEN: Токен для доступа к API Яндекс Практикума. Получить его можно, следуя этой ссылке
https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a
* TELEGRAM_TOKEN: Токен вашего Telegram-бота. Получить его можно через BotFather в Telegram.
* TELEGRAM_CHAT_ID: Идентификатор чата, куда бот будет отправлять уведомления. Получить его можно с помощью @userinfobot в Telegram.

### 6. Запустите бота
```bash
python homework.py
```