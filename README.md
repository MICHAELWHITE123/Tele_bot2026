# Warehouse Bot

Telegram бот + WebApp на FastAPI для управления складским оборудованием через Google Sheets.

## Технологии

- Python 3.13
- FastAPI
- aiogram 3.x
- Google Sheets API
- Docker
- Railway

## Структура проекта

```
Bot_wearehouse/
├── app/
│   ├── main.py          # FastAPI приложение
│   ├── bot.py           # Telegram бот
│   ├── google_sheets.py # Google Sheets клиент
│   └── config.py        # Конфигурация
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Локальная разработка

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GOOGLE_SERVICE_ACCOUNT_JSON=path/to/service_account.json
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
RAILWAY_ENV=development
```

### Запуск FastAPI

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Запуск бота (polling)

```bash
python -m app.bot
```

## Docker

### Сборка образа

```bash
docker build -t warehouse-bot .
```

### Запуск контейнера

```bash
docker run --env-file .env -p 8000:8000 warehouse-bot
```

Или с использованием docker-compose:

```bash
docker-compose up --build
```

### Проверка работы

После запуска контейнера проверьте:

```bash
curl http://localhost:8000/health
```

Ожидаемый ответ: `{"status":"ok"}`

## Деплой на Railway

### 1. Подготовка GitHub репозитория

1. Создайте репозиторий на GitHub
2. Инициализируйте git (если еще не сделано):

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/your-repo.git
git push -u origin main
```

### 2. Подключение Railway к репозиторию

1. Зайдите на [Railway](https://railway.app)
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"
4. Выберите ваш репозиторий
5. Railway автоматически определит Dockerfile и начнет сборку

### 3. Настройка переменных окружения в Railway

В настройках проекта Railway добавьте следующие переменные:

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | JSON содержимое service account файла (не путь!) | `{"type":"service_account","project_id":"..."}` |
| `GOOGLE_SPREADSHEET_ID` | ID Google таблицы | `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms` |
| `PORT` | Порт приложения (Railway устанавливает автоматически) | `8000` |
| `RAILWAY_ENV` | Окружение (production для Railway) | `production` |

**Важно для `GOOGLE_SERVICE_ACCOUNT_JSON`:**

В Railway нужно вставить **полное JSON содержимое** service account файла, а не путь к файлу. 

Пример:
1. Откройте ваш `service_account.json`
2. Скопируйте весь JSON (всю строку от `{` до `}`)
3. Вставьте в переменную `GOOGLE_SERVICE_ACCOUNT_JSON` в Railway

### 4. Настройка порта

Railway автоматически устанавливает переменную `PORT`. Dockerfile уже настроен для использования этой переменной:

```dockerfile
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### 5. Получение URL приложения

После деплоя Railway предоставит публичный URL вида:
```
https://your-app-name.up.railway.app
```

### 6. Настройка Telegram WebApp

В коде бота (`app/bot.py`) обновите URL WebApp для production:

```python
webapp_url = f"https://your-app-name.up.railway.app/webapp"
```

Или используйте переменную окружения `RAILWAY_PUBLIC_DOMAIN` (если доступна).

## Проверка деплоя

1. Проверьте health endpoint:
   ```
   https://your-app-name.up.railway.app/health
   ```

2. Проверьте WebApp:
   ```
   https://your-app-name.up.railway.app/webapp
   ```

3. Проверьте API:
   ```
   https://your-app-name.up.railway.app/items
   ```

## Структура Google Sheets

Проект работает с листом **ITEMS** в Google таблице:

- **Столбец K** - `inventory_id` (ключ поиска)
- **Столбец T** - чекбокс наклейки (можно менять)
- **Столбцы A-W** - данные оборудования (не изменяются)

## API Endpoints

- `GET /` - редирект на `/webapp`
- `GET /health` - проверка работоспособности
- `GET /webapp` - WebApp интерфейс
- `GET /items` - получить все элементы
- `GET /items/{inventory_id}` - получить элемент по ID
- `POST /items/check` - отметить элемент (установить T=TRUE)
- `POST /items/uncheck` - снять отметку (установить T=FALSE)

## Troubleshooting

### Ошибка при запуске контейнера

Проверьте, что все переменные окружения установлены:
```bash
docker run --env-file .env -p 8000:8000 warehouse-bot
```

### Ошибка подключения к Google Sheets

Убедитесь, что:
1. Service account JSON валиден
2. Service account имеет доступ к таблице
3. `GOOGLE_SPREADSHEET_ID` указан правильно

### Railway не запускается

Проверьте логи в Railway dashboard. Частые проблемы:
- Отсутствуют переменные окружения
- Неверный формат `GOOGLE_SERVICE_ACCOUNT_JSON` (должен быть JSON, а не путь)
- Порт не настроен (Railway устанавливает `PORT` автоматически)

## Лицензия

Проект для внутреннего использования.
