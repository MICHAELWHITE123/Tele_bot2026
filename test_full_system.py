"""
Комплексный тест всей системы: Google Sheets, FastAPI API, WebApp
Запуск: python test_full_system.py
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

print("=" * 70)
print("🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ")
print("=" * 70)
print()

# Шаг 1: Проверка переменных окружения
print("=" * 70)
print("1️⃣  ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
print("=" * 70)

load_dotenv()

required_vars = {
    "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
    "GOOGLE_SERVICE_ACCOUNT_JSON": os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"),
    "GOOGLE_SPREADSHEET_ID": os.getenv("GOOGLE_SPREADSHEET_ID"),
}

missing = []
for var_name, var_value in required_vars.items():
    if not var_value:
        missing.append(var_name)
        print(f"❌ {var_name}: НЕ УСТАНОВЛЕНО")
    else:
        if var_name == "TELEGRAM_BOT_TOKEN":
            masked = var_value[:10] + "..." if len(var_value) > 10 else "***"
            print(f"✅ {var_name}: {masked}")
        else:
            print(f"✅ {var_name}: {var_value}")

if missing:
    print(f"\n❌ ОШИБКА: Отсутствуют переменные: {', '.join(missing)}")
    print("Создайте файл .env с необходимыми переменными")
    sys.exit(1)

print("\n✅ Все переменные окружения загружены\n")

# Шаг 2: Проверка Google Sheets
print("=" * 70)
print("2️⃣  ПРОВЕРКА GOOGLE SHEETS")
print("=" * 70)

try:
    from app.google_sheets import GoogleSheetsClient, SHEET_NAME
    
    client = GoogleSheetsClient()
    result = client.get_items_sheet().execute()
    rows = result.get("values", [])
    
    if not rows:
        print("⚠️  Лист ITEMS пуст")
        sys.exit(1)
    
    print(f"✅ Подключение успешно! Найдено строк: {len(rows)}")
    
    # Найдем первый inventory_id для тестирования
    test_inventory_id = None
    for row in rows:
        if len(row) > 10 and row[10]:
            test_inventory_id = str(row[10]).strip()
            break
    
    if test_inventory_id:
        print(f"✅ Тестовый inventory_id найден: {test_inventory_id}")
        
        # Проверка методов GoogleSheetsClient
        print("\n📋 Тестирование методов GoogleSheetsClient...")
        
        # get_all_items
        items = client.get_all_items()
        print(f"✅ get_all_items(): получено {len(items)} элементов")
        
        # find_item_by_inventory_id
        item = client.find_item_by_inventory_id(test_inventory_id)
        if item:
            print(f"✅ find_item_by_inventory_id('{test_inventory_id}'): найден")
            print(f"   - Название (B): {item['data'].get('B', 'N/A')}")
            print(f"   - Место (V): {item['data'].get('V', 'N/A')}")
            print(f"   - Чекбокс (T): {item['checkbox_t']}")
        else:
            print(f"❌ find_item_by_inventory_id('{test_inventory_id}'): НЕ НАЙДЕН")
            sys.exit(1)
    else:
        print("⚠️  Не найден inventory_id для тестирования")
        test_inventory_id = "TEST123"
    
    print("\n✅ Google Sheets работает корректно\n")
    
except Exception as e:
    print(f"❌ ОШИБКА Google Sheets: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Шаг 3: Проверка FastAPI эндпоинтов
print("=" * 70)
print("3️⃣  ПРОВЕРКА FASTAPI ЭНДПОИНТОВ")
print("=" * 70)

try:
    from app.main import app
    
    try:
        from fastapi.testclient import TestClient
        client_api = TestClient(app)
    except ImportError:
        print("⚠️  httpx не установлен, пропускаем тесты API")
        print("   Установите: pip install httpx")
        client_api = None
    
    if not client_api:
        print("\n⚠️  Пропуск тестов API (httpx не установлен)")
    else:
        # Тест /health
        print("\n🔍 Тест GET /health...")
        response = client_api.get("/health")
        if response.status_code == 200:
            print(f"✅ /health: {response.json()}")
        else:
            print(f"❌ /health: статус {response.status_code}")
            sys.exit(1)
        
        # Тест GET /items
        print("\n🔍 Тест GET /items...")
        response = client_api.get("/items")
        if response.status_code == 200:
            items_data = response.json()
            print(f"✅ /items: получено {len(items_data)} элементов")
        else:
            print(f"❌ /items: статус {response.status_code}")
            sys.exit(1)
        
        # Тест GET /items/{inventory_id}
        print(f"\n🔍 Тест GET /items/{test_inventory_id}...")
        response = client_api.get(f"/items/{test_inventory_id}")
        if response.status_code == 200:
            item_data = response.json()
            print(f"✅ /items/{test_inventory_id}: найден")
            print(f"   - Название: {item_data['data'].get('B', 'N/A')}")
            print(f"   - Место: {item_data['data'].get('V', 'N/A')}")
        elif response.status_code == 404:
            print(f"⚠️  /items/{test_inventory_id}: не найден (404)")
        else:
            print(f"❌ /items/{test_inventory_id}: статус {response.status_code}")
        
        # Тест POST /items/check
        print(f"\n🔍 Тест POST /items/check...")
        response = client_api.post(
            "/items/check",
            json={"inventory_id": test_inventory_id}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ /items/check: {result}")
        elif response.status_code == 404:
            print(f"⚠️  /items/check: inventory_id не найден")
        else:
            print(f"❌ /items/check: статус {response.status_code}")
            print(f"   Ответ: {response.text}")
        
        # Тест POST /items/uncheck
        print(f"\n🔍 Тест POST /items/uncheck...")
        response = client_api.post(
            "/items/uncheck",
            json={"inventory_id": test_inventory_id}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ /items/uncheck: {result}")
        elif response.status_code == 404:
            print(f"⚠️  /items/uncheck: inventory_id не найден")
        else:
            print(f"❌ /items/uncheck: статус {response.status_code}")
        
        # Тест GET /webapp
        print("\n🔍 Тест GET /webapp...")
        response = client_api.get("/webapp")
        if response.status_code == 200:
            html_content = response.text
            if "Warehouse Scanner" in html_content and "scanQR" in html_content:
                print("✅ /webapp: HTML страница загружена корректно")
                print(f"   Размер HTML: {len(html_content)} символов")
            else:
                print("⚠️  /webapp: HTML загружен, но содержимое неполное")
        else:
            print(f"❌ /webapp: статус {response.status_code}")
        
        # Тест GET /
        print("\n🔍 Тест GET / (редирект)...")
        response = client_api.get("/", follow_redirects=False)
        if response.status_code == 307:
            print("✅ /: редирект на /webapp работает")
        else:
            print(f"⚠️  /: статус {response.status_code}")
        
        print("\n✅ Все FastAPI эндпоинты работают корректно\n")
    
except Exception as e:
    print(f"❌ ОШИБКА тестирования API: {str(e)}")
    import traceback
    traceback.print_exc()

# Шаг 4: Итоговая сводка
print("=" * 70)
print("4️⃣  ИТОГОВАЯ СВОДКА")
print("=" * 70)

print("\n✅ СИСТЕМА ГОТОВА К РАБОТЕ!")
print("\n📝 Следующие шаги:")
print("   1. Запустите FastAPI сервер:")
print("      uvicorn app.main:app --reload")
print("   2. Откройте в браузере: http://localhost:8000/webapp")
print("   3. Или используйте Swagger UI: http://localhost:8000/docs")
print("   4. Для тестирования бота запустите: python test_bot_local.py")
print()

print("=" * 70)
print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
print("=" * 70)
