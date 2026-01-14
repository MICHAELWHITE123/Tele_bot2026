import asyncio
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup

from app.config import config
from app.google_sheets import get_sheets_client, SHEET_NAME

router = Router()

WEBAPP_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QR Scanner</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--tg-theme-bg-color, #1a1a2e);
            color: var(--tg-theme-text-color, #eaeaea);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        h1 {
            font-size: 1.5rem;
            margin-bottom: 20px;
            color: var(--tg-theme-hint-color, #a0a0a0);
        }
        .container {
            width: 100%;
            max-width: 400px;
        }
        input {
            width: 100%;
            padding: 16px;
            font-size: 1.1rem;
            border: 2px solid var(--tg-theme-hint-color, #444);
            border-radius: 12px;
            background: var(--tg-theme-secondary-bg-color, #16213e);
            color: var(--tg-theme-text-color, #eaeaea);
            margin-bottom: 16px;
            outline: none;
            transition: border-color 0.2s;
        }
        input:focus {
            border-color: var(--tg-theme-button-color, #0f4c75);
        }
        button {
            width: 100%;
            padding: 16px;
            font-size: 1.1rem;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            background: var(--tg-theme-button-color, #3282b8);
            color: var(--tg-theme-button-text-color, #fff);
            cursor: pointer;
            transition: opacity 0.2s;
        }
        button:active { opacity: 0.8; }
        .status {
            margin-top: 20px;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            display: none;
        }
        .status.show { display: block; }
        .status.success { background: #1b4332; color: #95d5b2; }
        .status.error { background: #4a1c1c; color: #f8a5a5; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Warehouse QR Scanner</h1>
        <input type="text" id="inventoryId" placeholder="Enter inventory_id from QR">
        <button onclick="sendData()">Submit</button>
        <div id="status" class="status"></div>
    </div>
    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();

        function sendData() {
            const inventoryId = document.getElementById('inventoryId').value.trim();
            const statusEl = document.getElementById('status');
            if (!inventoryId) {
                statusEl.className = 'status show error';
                statusEl.textContent = 'Please enter inventory_id';
                return;
            }
            tg.sendData(inventoryId);
            statusEl.className = 'status show success';
            statusEl.textContent = 'Sent: ' + inventoryId;
        }
    </script>
</body>
</html>
"""


async def find_row_by_inventory_id(inventory_id: str) -> tuple[int, str, str] | None:
    """Find row index by inventory_id in column K. Returns (1-based index, equipment name from B, storage location from V) or None."""
    client = get_sheets_client()
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
    """Update column T (index 19) to TRUE for given row. Returns success status."""
    client = get_sheets_client()
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
    """Get item information by inventory_id. Returns (success, message, row_index)."""
    try:
        result = await find_row_by_inventory_id(inventory_id)
        
        if result is None:
            return False, f"❌ Item not found: {inventory_id}", None
        
        row_index, equipment_name, storage_location = result
        
        message = (
            f"📦 <b>Equipment:</b> {equipment_name}\n"
            f"📍 <b>Storage location:</b> {storage_location}\n"
            f"🆔 <b>Inventory ID:</b> {inventory_id}\n"
            f"📊 <b>Row:</b> {row_index}"
        )
        return True, message, row_index
    
    except Exception as e:
        return False, f"❌ Error processing: {str(e)}", None


async def mark_label(row_index: int) -> tuple[bool, str]:
    """Mark label in column T for specified row. Returns (success, message)."""
    try:
        await update_column_t(row_index)
        return True, "✅ Label marked in table"
    except Exception as e:
        return False, f"❌ Error marking: {str(e)}"


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Handle /start command."""
    webapp_url = f"https://{config.RAILWAY_ENV}.up.railway.app/webapp" if config.is_production() else "http://localhost:8000/webapp"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📷 Open QR Scanner", web_app=WebAppInfo(url=webapp_url))]
    ])
    
    await message.answer(
        "🏭 <b>Warehouse Bot</b>\n\n"
        "Send inventory_id from QR code as text message,\n"
        "or use the scanner below:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.message()
async def handle_message(message: types.Message):
    """Handle text messages as QR code data (inventory_id)."""
    if not message.text:
        return
    
    inventory_id = message.text.strip()
    
    if not inventory_id:
        await message.answer("❌ Empty message")
        return
    
    await message.answer(f"🔍 Searching for: {inventory_id}...")
    
    success, info_message, row_index = await get_item_info(inventory_id)
    
    if not success:
        await message.answer(info_message)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Mark label", callback_data=f"mark_{row_index}")]
    ])
    
    await message.answer(info_message, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("mark_"))
async def handle_mark_callback(callback: types.CallbackQuery):
    """Handle 'Mark label' button click."""
    try:
        row_index = int(callback.data.split("_")[1])
        
        success, result_message = await mark_label(row_index)
        
        if success:
            await callback.answer("✅ Label marked!")
            await callback.message.edit_text(
                callback.message.text + f"\n\n{result_message}",
                parse_mode="HTML"
            )
        else:
            await callback.answer(result_message, show_alert=True)
    
    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)


bot: Bot | None = None
dp: Dispatcher | None = None


def get_bot() -> Bot:
    """Get or create Bot instance."""
    global bot
    if bot is None:
        if not config.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    return bot


def get_dispatcher() -> Dispatcher:
    """Get or create Dispatcher instance."""
    global dp
    if dp is None:
        dp = Dispatcher()
        dp.include_router(router)
    return dp


async def start_polling():
    """Start bot in polling mode (for development)."""
    bot_instance = get_bot()
    dispatcher = get_dispatcher()
    await dispatcher.start_polling(bot_instance)


async def process_webhook_update(update_data: dict):
    """Process incoming webhook update from Telegram."""
    bot_instance = get_bot()
    dispatcher = get_dispatcher()
    update = types.Update.model_validate(update_data)
    await dispatcher.feed_update(bot=bot_instance, update=update)
