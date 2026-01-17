# Инструкции по исправлению ошибки Content-Length в WebApp

## Проблема
Ошибка: `h11._util.LocalProtocolError: Too much data for declared Content-Length`

Эта ошибка возникает, когда фактический размер тела ответа не совпадает с заголовком `Content-Length`, который установил Starlette/FastAPI.

## Причины и решения

### ШАГ 1: Проверка текущего решения
**Текущее решение:** Используется `StreamingResponse` с разбиением на chunks и явным удалением `Content-Length`.

**Если это не помогло, переходите к ШАГУ 2.**

---

### ШАГ 2: Использование FileResponse (рекомендуется)
**Проблема:** Starlette автоматически вычисляет `Content-Length` для строк/байтов, что вызывает ошибку.

**Решение:** Сохранить HTML в временный файл и использовать `FileResponse`, который не требует `Content-Length`.

**Промт для Cursor:**
```
Измени endpoint /webapp в app/main.py:
1. Импортируй FileResponse и tempfile
2. Создай временный файл с HTML контентом
3. Верни FileResponse с путем к файлу
4. Убедись, что файл создается в памяти (BytesIO) или используй NamedTemporaryFile с delete=False
```

**Код:**
```python
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile
import os

@app.get("/webapp")
async def webapp(request: Request):
    base_url = str(request.base_url).rstrip("/")
    html_content = html_template.replace('BASE_URL_PLACEHOLDER', base_url)
    
    # Create temporary file
    with NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name
    
    return FileResponse(
        temp_path,
        media_type="text/html; charset=utf-8",
        filename="webapp.html"
    )
```

---

### ШАГ 3: Использование Jinja2 Templates
**Проблема:** Встроенный HTML в коде может вызывать проблемы с кодировкой.

**Решение:** Вынести HTML в отдельный файл и использовать Jinja2.

**Промт для Cursor:**
```
1. Установи jinja2 в requirements.txt
2. Создай папку templates/ в корне проекта
3. Создай файл templates/webapp.html с HTML контентом
4. В app/main.py используй Jinja2Templates для рендеринга
5. Замени BASE_URL_PLACEHOLDER на {{ base_url }} в шаблоне
```

**Код:**
```python
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@app.get("/webapp")
async def webapp(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return templates.TemplateResponse(
        "webapp.html",
        {"request": request, "base_url": base_url}
    )
```

---

### ШАГ 4: Использование кастомного ASGI middleware
**Проблема:** Starlette автоматически добавляет `Content-Length` для всех ответов.

**Решение:** Создать middleware, который удаляет `Content-Length` для `/webapp`.

**Промт для Cursor:**
```
Создай middleware в app/main.py:
1. Создай класс WebAppMiddleware
2. В process_response удаляй Content-Length для пути /webapp
3. Добавь middleware в app через app.add_middleware()
```

**Код:**
```python
from starlette.middleware.base import BaseHTTPMiddleware

class RemoveContentLengthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path == "/webapp":
            response.headers.pop("content-length", None)
        return response

app.add_middleware(RemoveContentLengthMiddleware)
```

---

### ШАГ 5: Использование uvicorn с другими настройками
**Проблема:** Uvicorn может неправильно обрабатывать ответы.

**Решение:** Изменить настройки запуска uvicorn.

**Промт для Cursor:**
```
В start_all.py или start_server.py измени запуск uvicorn:
1. Добавь параметр --no-access-log
2. Добавь параметр --limit-max-requests 10000
3. Попробуй использовать --http httptools вместо h11
```

**Код:**
```python
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=port,
    log_level="info",
    access_log=False,
    limit_max_requests=10000
)
```

---

### ШАГ 6: Проверка версий библиотек
**Проблема:** Несовместимость версий FastAPI/Starlette/Uvicorn.

**Промт для Cursor:**
```
Проверь requirements.txt и обнови версии:
1. fastapi>=0.104.0
2. uvicorn[standard]>=0.24.0
3. starlette>=0.27.0
4. Убедись, что нет конфликтов версий
```

---

### ШАГ 7: Альтернативное решение - статический файл
**Проблема:** Все динамические решения не работают.

**Решение:** Создать статический HTML файл и отдавать его через статику.

**Промт для Cursor:**
```
1. Создай папку static/ в корне проекта
2. Создай файл static/webapp.html с HTML (без BASE_URL_PLACEHOLDER)
3. В app/main.py используй StaticFiles для /static
4. В endpoint /webapp делай редирект на /static/webapp.html
5. Используй JavaScript для получения base_url из window.location
```

**Код:**
```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/webapp")
async def webapp(request: Request):
    return RedirectResponse(url="/static/webapp.html")
```

В JavaScript:
```javascript
const API_BASE_URL = window.location.origin;
```

---

## Рекомендуемый порядок действий

1. **Попробуйте ШАГ 2 (FileResponse)** - самое простое и надежное решение
2. Если не помогло - **ШАГ 3 (Jinja2)** - более правильный подход для шаблонов
3. Если не помогло - **ШАГ 4 (Middleware)** - обходной путь
4. Если не помогло - **ШАГ 7 (Статический файл)** - самое надежное решение

## Проверка после исправления

После каждого шага проверьте:
1. Запустите приложение локально
2. Откройте `/webapp` в браузере
3. Проверьте логи на наличие ошибок
4. Проверьте Network tab в DevTools - заголовки ответа

## Дополнительная диагностика

Если ничего не помогает:
1. Проверьте логи Railway на наличие других ошибок
2. Проверьте размер HTML контента (может быть слишком большой)
3. Проверьте кодировку файлов (должна быть UTF-8)
4. Попробуйте упростить HTML (убрать часть стилей/скриптов) для теста
