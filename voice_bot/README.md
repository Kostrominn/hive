# Voice Bot

Телеграм-бот, который принимает голосовые сообщения, сохраняет их на Google Drive и отвечает одним из заранее подготовленных сообщений.

## Запуск

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Подготовьте файл учетных данных Google Service Account и сохраните его как `service_account.json` в корне проекта или укажите путь в переменной `GOOGLE_APPLICATION_CREDENTIALS`.

3. Установите идентификатор папки на Google Drive в переменной окружения `GOOGLE_DRIVE_FOLDER_ID`. По умолчанию используется корневая папка.

4. Запустите бота:

```bash
python bot.py
```
