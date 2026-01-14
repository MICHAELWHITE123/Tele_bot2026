"""
Локальный тестовый скрипт для Telegram бота с Google Sheets.
Запуск: python test_bot_local.py
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.google_sheets import GoogleSheetsClient, SHEET_NAME
from app.config import config


def check_env():
    """Проверка наличия всех необходимых переменных окружения."""
    print("=" * 60)
    print("Проверка переменных окружения...")
    print("=" * 60)
    
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
        print("\n❌ ОШИБКА: Отсутствуют обязательные переменные окружения!")
        print("Создайте файл .env на основе .env.example")
        return False
    
    print("\n✅ Все переменные окружения загружены успешно\n")
    return True


def check_google_sheets():
    """Проверка подключения к Google Sheets и вывод первых 5 строк."""
    print("=" * 60)
    print("Проверка подключения к Google Sheets...")
    print("=" * 60)
    
    try:
        client = GoogleSheetsClient()
        result = client.get_items_sheet().execute()
        rows = result.get("values", [])
        
        if not rows:
            print("⚠️  Лист ITEMS пуст")
            return False
        
        print(f"✅ Подключение успешно! Найдено строк: {len(rows)}")
        print(f"\nПервые 5 строк листа '{SHEET_NAME}':")
        print("-" * 60)
        
        for idx, row in enumerate(rows[:5], 1):
            inventory_id = row[10] if len(row) > 10 else "N/A"
            checkbox_t = row[19] if len(row) > 19 else "N/A"
            print(f"Строка {idx}:")
            print(f"  Column K (inventory_id): {inventory_id}")
            print(f"  Column T (чекбокс): {checkbox_t}")
            print()
        
        if len(rows) > 5:
            print(f"... и еще {len(rows) - 5} строк(и)\n")
        
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА подключения к Google Sheets: {str(e)}")
        print("\nПроверьте:")
        print("1. Путь к service_account.json корректен")
        print("2. Файл service_account.json существует и валиден")
        print("3. GOOGLE_SPREADSHEET_ID указан правильно")
        print("4. Service account имеет доступ к таблице")
        return False


async def find_row_by_inventory_id(inventory_id: str) -> tuple[int, str, str] | None:
    """Найти индекс строки по inventory_id в столбце K. Возвращает (1-based индекс, название из B, место из V) или None."""
    client = GoogleSheetsClient()
    result = client.get_items_sheet().execute()
    rows = result.get("values", [])
    
    for idx, row in enumerate(rows):
        if len(row) > 10:
            cell_k = row[10]
            if str(cell_k).strip() == str(inventory_id).strip():
                equipment_name = row[1] if len(row) > 1 else "N/A"
                storage_location = row[21] if len(row) > 21 else "N/A"
                return (idx + 1, equipment_name, storage_location)
    return None


async def update_column_t(row_index: int) -> bool:
    """Обновить столбец T (индекс 19) на TRUE для указанной строки."""
    client = GoogleSheetsClient()
    range_notation = f"{SHEET_NAME}!T{row_index}"
    
    body = {"values": [[True]]}
    
    client._sheets.values().update(
        spreadsheetId=client._spreadsheet_id,
        range=range_notation,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    
    return True


async def get_item_info(inventory_id: str) -> tuple[bool, str, int | None]:
    """Получить информацию о товаре по inventory_id. Возвращает (успех, сообщение, row_index)."""
    try:
        result = await find_row_by_inventory_id(inventory_id)
        
        if result is None:
            return False, f"❌ Товар не найден: {inventory_id}", None
        
        row_index, equipment_name, storage_location = result
        
        message = (
            f"📦 <b>Оборудование:</b> {equipment_name}\n"
            f"📍 <b>Место хранения:</b> {storage_location}\n"
            f"🆔 <b>Inventory ID:</b> {inventory_id}\n"
            f"📊 <b>Строка:</b> {row_index}"
        )
        return True, message, row_index
    
    except Exception as e:
        return False, f"❌ Ошибка обработки: {str(e)}", None


async def mark_label(row_index: int) -> tuple[bool, str]:
    """Проставить галочку в столбце T для указанной строки. Возвращает (успех, сообщение)."""
    try:
        await update_column_t(row_index)
        return True, "✅ Наклейка отмечена в таблице"
    except Exception as e:
        return False, f"❌ Ошибка при отметке: {str(e)}"


router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработчик команды /start."""
    await message.answer(
        "🏭 <b>Warehouse Bot (Локальный тест)</b>\n\n"
        "Отправьте inventory_id из QR кода как текстовое сообщение.\n"
        "Бот найдет товар в Google Sheets и поставит галочку в столбце T.",
        parse_mode="HTML"
    )


@router.message()
async def handle_message(message: types.Message):
    """Обработчик текстовых сообщений как данных QR кода (inventory_id)."""
    if not message.text:
        return
    
    inventory_id = message.text.strip()
    
    if not inventory_id:
        await message.answer("❌ Пустое сообщение")
        return
    
    print(f"\n📨 Получено сообщение от {message.from_user.id}: {inventory_id}")
    await message.answer(f"🔍 Поиск: {inventory_id}...")
    
    success, info_message, row_index = await get_item_info(inventory_id)
    
    if not success:
        await message.answer(info_message)
        return
    
    print(f"📤 Найдено: {info_message}")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отметить наклейку", callback_data=f"mark_{row_index}")]
    ])
    
    await message.answer(info_message, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("mark_"))
async def handle_mark_callback(callback: types.CallbackQuery):
    """Обработчик нажатия кнопки 'Отметить наклейку'."""
    try:
        row_index = int(callback.data.split("_")[1])
        
        success, result_message = await mark_label(row_index)
        
        if success:
            await callback.answer("✅ Наклейка отмечена!")
            await callback.message.edit_text(
                callback.message.text + f"\n\n{result_message}",
                parse_mode="HTML"
            )
        else:
            await callback.answer(result_message, show_alert=True)
    
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


async def main():
    """Главная функция для запуска бота в режиме polling."""
    print("\n" + "=" * 60)
    print("🤖 ЗАПУСК ЛОКАЛЬНОГО ТЕСТОВОГО БОТА")
    print("=" * 60 + "\n")
    
    if not check_env():
        sys.exit(1)
    
    if not check_google_sheets():
        sys.exit(1)
    
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден после загрузки .env")
        sys.exit(1)
    
    print("=" * 60)
    print("🤖 Инициализация бота...")
    print("=" * 60)
    
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    
    print("✅ Бот инициализирован")
    print("✅ Ожидание сообщений...")
    print("✅ Для остановки нажмите Ctrl+C\n")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("\n\n⏹️  Остановка бота...")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 До свидания!")
