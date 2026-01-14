from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel

from app.google_sheets import get_sheets_client

app = FastAPI(
    title="Warehouse Bot WebApp API",
    description="REST API for managing warehouse items and labels in Google Sheets",
    version="1.0.0"
)


class CheckRequest(BaseModel):
    inventory_id: str


class CheckResponse(BaseModel):
    status: str
    inventory_id: str


@app.get("/")
async def root():
    """Root endpoint - redirects to webapp."""
    return RedirectResponse(url="/webapp")


@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint."""
    return JSONResponse(content={}, status_code=204)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/items", response_model=list[dict])
async def get_all_items():
    """
    Get all items from ITEMS sheet.
    Returns list of items with their data and checkbox status.
    """
    try:
        client = get_sheets_client()
        items = client.get_all_items()
        return items
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "internal server error"}
        )


@app.get("/items/{inventory_id}", response_model=dict)
async def get_item_by_id(inventory_id: str):
    """
    Get item by inventory_id.
    Returns item data if found, 404 if not found.
    """
    try:
        client = get_sheets_client()
        item = client.find_item_by_inventory_id(inventory_id)
        
        if item is None:
            return JSONResponse(
                status_code=404,
                content={"error": "inventory_id not found"}
            )
        
        return item
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "internal server error"}
        )


@app.post("/items/check", response_model=CheckResponse)
async def check_item(request: CheckRequest):
    """
    Mark item checkbox (column T) as TRUE.
    Accepts inventory_id in request body.
    """
    try:
        client = get_sheets_client()
        item = client.find_item_by_inventory_id(request.inventory_id)
        
        if item is None:
            return JSONResponse(
                status_code=404,
                content={"error": "inventory_id not found"}
            )
        
        client.update_checkbox(item["row_index"], True)
        
        return CheckResponse(
            status="ok",
            inventory_id=request.inventory_id
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "internal server error"}
        )


@app.post("/items/uncheck", response_model=CheckResponse)
async def uncheck_item(request: CheckRequest):
    """
    Mark item checkbox (column T) as FALSE.
    Accepts inventory_id in request body.
    """
    try:
        client = get_sheets_client()
        item = client.find_item_by_inventory_id(request.inventory_id)
        
        if item is None:
            return JSONResponse(
                status_code=404,
                content={"error": "inventory_id not found"}
            )
        
        client.update_checkbox(item["row_index"], False)
        
        return CheckResponse(
            status="ok",
            inventory_id=request.inventory_id
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "internal server error"}
        )


@app.get("/webapp", response_class=HTMLResponse)
async def webapp(request: Request):
    """WebApp interface for QR scanning and item management."""
    base_url = str(request.base_url).rstrip("/")
    
    html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Warehouse Scanner</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--tg-theme-bg-color, #ffffff);
            color: var(--tg-theme-text-color, #000000);
            min-height: 100vh;
            padding: 16px;
            padding-bottom: 80px;
        }}
        
        .container {{
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 24px;
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: 600;
            color: var(--tg-theme-text-color, #000000);
            margin-bottom: 8px;
        }}
        
        .header p {{
            font-size: 14px;
            color: var(--tg-theme-hint-color, #999999);
        }}
        
        .scan-section {{
            background: var(--tg-theme-secondary-bg-color, #f0f0f0);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .input-group {{
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
        }}
        
        .input-group input {{
            flex: 1;
            padding: 14px 16px;
            font-size: 16px;
            border: 2px solid var(--tg-theme-hint-color, #e0e0e0);
            border-radius: 12px;
            background: var(--tg-theme-bg-color, #ffffff);
            color: var(--tg-theme-text-color, #000000);
            outline: none;
            transition: border-color 0.2s;
        }}
        
        .input-group input:focus {{
            border-color: var(--tg-theme-button-color, #3390ec);
        }}
        
        .btn {{
            padding: 14px 24px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        
        .btn-primary {{
            background: var(--tg-theme-button-color, #3390ec);
            color: var(--tg-theme-button-text-color, #ffffff);
        }}
        
        .btn-primary:active {{
            opacity: 0.8;
            transform: scale(0.98);
        }}
        
        .btn-secondary {{
            background: var(--tg-theme-secondary-bg-color, #f0f0f0);
            color: var(--tg-theme-text-color, #000000);
        }}
        
        .btn-secondary:active {{
            opacity: 0.8;
        }}
        
        .btn-success {{
            background: #4caf50;
            color: #ffffff;
        }}
        
        .btn-danger {{
            background: #f44336;
            color: #ffffff;
        }}
        
        .btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        .item-card {{
            background: var(--tg-theme-secondary-bg-color, #f0f0f0);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: none;
        }}
        
        .item-card.show {{
            display: block;
            animation: slideIn 0.3s ease-out;
        }}
        
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateY(-10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .item-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--tg-theme-hint-color, #e0e0e0);
        }}
        
        .item-title {{
            font-size: 20px;
            font-weight: 600;
            color: var(--tg-theme-text-color, #000000);
        }}
        
        .item-status {{
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .item-status.checked {{
            background: #4caf50;
            color: #ffffff;
        }}
        
        .item-status.unchecked {{
            background: #ff9800;
            color: #ffffff;
        }}
        
        .item-info {{
            margin-bottom: 16px;
        }}
        
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid var(--tg-theme-hint-color, #e0e0e0);
        }}
        
        .info-row:last-child {{
            border-bottom: none;
        }}
        
        .info-label {{
            font-size: 14px;
            color: var(--tg-theme-hint-color, #999999);
            font-weight: 500;
        }}
        
        .info-value {{
            font-size: 14px;
            color: var(--tg-theme-text-color, #000000);
            font-weight: 600;
            text-align: right;
            max-width: 60%;
            word-break: break-word;
        }}
        
        .item-actions {{
            display: flex;
            gap: 12px;
            margin-top: 16px;
        }}
        
        .item-actions .btn {{
            flex: 1;
        }}
        
        .status-message {{
            padding: 12px 16px;
            border-radius: 12px;
            margin-top: 12px;
            text-align: center;
            font-size: 14px;
            font-weight: 500;
            display: none;
        }}
        
        .status-message.show {{
            display: block;
            animation: fadeIn 0.3s ease-out;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .status-message.success {{
            background: #e8f5e9;
            color: #2e7d32;
        }}
        
        .status-message.error {{
            background: #ffebee;
            color: #c62828;
        }}
        
        .status-message.loading {{
            background: #e3f2fd;
            color: #1565c0;
        }}
        
        .loading-spinner {{
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid currentColor;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        .empty-state {{
            text-align: center;
            padding: 40px 20px;
            color: var(--tg-theme-hint-color, #999999);
        }}
        
        .empty-state-icon {{
            font-size: 48px;
            margin-bottom: 16px;
        }}
        
        .empty-state-text {{
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏭 Warehouse Scanner</h1>
            <p>Сканируйте QR-код или введите inventory_id</p>
        </div>
        
        <div class="scan-section">
            <button class="btn btn-primary" onclick="scanQR()" style="width: 100%; margin-bottom: 12px;">
                📷 Сканировать QR-код
            </button>
            <div class="input-group">
                <input 
                    type="text" 
                    id="inventoryId" 
                    placeholder="Или введите inventory_id вручную"
                    autocomplete="off"
                >
            </div>
            <button class="btn btn-primary" onclick="searchItem()" style="width: 100%;">
                🔍 Найти оборудование
            </button>
            <div id="statusMessage" class="status-message"></div>
        </div>
        
        <div id="itemCard" class="item-card">
            <div class="item-header">
                <div class="item-title" id="itemTitle">Оборудование</div>
                <div class="item-status" id="itemStatus">Не проверено</div>
            </div>
            <div class="item-info">
                <div class="info-row">
                    <span class="info-label">📦 Название:</span>
                    <span class="info-value" id="itemName">—</span>
                </div>
                <div class="info-row">
                    <span class="info-label">📍 Место хранения:</span>
                    <span class="info-value" id="itemLocation">—</span>
                </div>
                <div class="info-row">
                    <span class="info-label">🆔 Inventory ID:</span>
                    <span class="info-value" id="itemInventoryId">—</span>
                </div>
            </div>
            <div class="item-actions">
                <button class="btn btn-success" onclick="checkItem()" id="checkBtn">
                    ✅ Отметить
                </button>
                <button class="btn btn-danger" onclick="uncheckItem()" id="uncheckBtn">
                    ❌ Снять отметку
                </button>
            </div>
        </div>
        
        <div id="emptyState" class="empty-state">
            <div class="empty-state-icon">📦</div>
            <div class="empty-state-text">Введите или отсканируйте inventory_id</div>
        </div>
    </div>
    
    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        
        const API_BASE_URL = '{base_url}';
        let currentItem = null;
        
        console.log('WebApp initialized. API_BASE_URL:', API_BASE_URL);
        console.log('Telegram WebApp platform:', tg.platform);
        
        function showStatus(message, type = 'loading') {{
            const statusEl = document.getElementById('statusMessage');
            statusEl.textContent = message;
            statusEl.className = `status-message show ${{type}}`;
            
            if (type !== 'loading') {{
                setTimeout(() => {{
                    statusEl.classList.remove('show');
                }}, 3000);
            }}
        }}
        
        function hideStatus() {{
            const statusEl = document.getElementById('statusMessage');
            statusEl.classList.remove('show');
        }}
        
        function scanQR() {{
            console.log('scanQR called, platform:', tg.platform);
            
            if (tg.platform === 'unknown') {{
                showStatus('Сканирование QR доступно только в Telegram', 'error');
                return;
            }}
            
            if (!tg.showScanQrPopup) {{
                console.error('showScanQrPopup not available');
                showStatus('Сканирование QR недоступно в этой версии Telegram', 'error');
                return;
            }}
            
            try {{
                tg.showScanQrPopup({{
                    text: 'Наведите камеру на QR-код'
                }}, (text) => {{
                    console.log('QR scan result:', text);
                    if (text && text.trim()) {{
                        const inventoryId = text.trim();
                        document.getElementById('inventoryId').value = inventoryId;
                        searchItem();
                    }} else {{
                        showStatus('QR-код не распознан. Попробуйте еще раз.', 'error');
                    }}
                }});
            }} catch (error) {{
                console.error('QR scan error:', error);
                showStatus('Ошибка при сканировании QR: ' + error.message, 'error');
            }}
        }}
        
        async function searchItem() {{
            const inventoryId = document.getElementById('inventoryId').value.trim();
            
            if (!inventoryId) {{
                showStatus('Введите inventory_id', 'error');
                return;
            }}
            
            showStatus('Поиск оборудования...', 'loading');
            
            const url = `${{API_BASE_URL}}/items/${{inventoryId}}`;
            console.log('Searching item, URL:', url);
            
            try {{
                const response = await fetch(url);
                console.log('Response status:', response.status);
                
                if (response.status === 404) {{
                    const error = await response.json();
                    showStatus(`Оборудование не найдено: ${{inventoryId}}`, 'error');
                    hideItemCard();
                    return;
                }}
                
                if (!response.ok) {{
                    const errorText = await response.text();
                    console.error('Server error:', errorText);
                    throw new Error(`Ошибка сервера: ${{response.status}}`);
                }}
                
                const item = await response.json();
                console.log('Item found:', item);
                currentItem = item;
                displayItem(item);
                hideStatus();
                
            }} catch (error) {{
                console.error('Search error:', error);
                showStatus('Ошибка при поиске оборудования: ' + error.message, 'error');
            }}
        }}
        
        function displayItem(item) {{
            const card = document.getElementById('itemCard');
            const emptyState = document.getElementById('emptyState');
            
            document.getElementById('itemTitle').textContent = item.data?.B || 'Оборудование';
            document.getElementById('itemName').textContent = item.data?.B || '—';
            document.getElementById('itemLocation').textContent = item.data?.V || '—';
            document.getElementById('itemInventoryId').textContent = item.inventory_id || '—';
            
            const statusEl = document.getElementById('itemStatus');
            if (item.checkbox_t) {{
                statusEl.textContent = 'Отмечено';
                statusEl.className = 'item-status checked';
            }} else {{
                statusEl.textContent = 'Не отмечено';
                statusEl.className = 'item-status unchecked';
            }}
            
            card.classList.add('show');
            emptyState.style.display = 'none';
        }}
        
        function hideItemCard() {{
            const card = document.getElementById('itemCard');
            const emptyState = document.getElementById('emptyState');
            card.classList.remove('show');
            emptyState.style.display = 'block';
            currentItem = null;
        }}
        
        async function checkItem() {{
            if (!currentItem) return;
            
            const btn = document.getElementById('checkBtn');
            btn.disabled = true;
            showStatus('Обновление...', 'loading');
            
            try {{
                const response = await fetch(`${{API_BASE_URL}}/items/check`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        inventory_id: currentItem.inventory_id
                    }})
                }});
                
                if (!response.ok) {{
                    const error = await response.json();
                    throw new Error(error.error || 'Ошибка обновления');
                }}
                
                const result = await response.json();
                currentItem.checkbox_t = true;
                displayItem(currentItem);
                showStatus('✅ Отметка установлена', 'success');
                
            }} catch (error) {{
                showStatus('Ошибка при обновлении', 'error');
                console.error('Check error:', error);
            }} finally {{
                btn.disabled = false;
            }}
        }}
        
        async function uncheckItem() {{
            if (!currentItem) return;
            
            const btn = document.getElementById('uncheckBtn');
            btn.disabled = true;
            showStatus('Обновление...', 'loading');
            
            try {{
                const response = await fetch(`${{API_BASE_URL}}/items/uncheck`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        inventory_id: currentItem.inventory_id
                    }})
                }});
                
                if (!response.ok) {{
                    const error = await response.json();
                    throw new Error(error.error || 'Ошибка обновления');
                }}
                
                const result = await response.json();
                currentItem.checkbox_t = false;
                displayItem(currentItem);
                showStatus('❌ Отметка снята', 'success');
                
            }} catch (error) {{
                showStatus('Ошибка при обновлении', 'error');
                console.error('Uncheck error:', error);
            }} finally {{
                btn.disabled = false;
            }}
        }}
        
        document.getElementById('inventoryId').addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') {{
                searchItem();
            }}
        }});
        
        // Проверка доступности API при загрузке
        async function checkAPI() {{
            try {{
                const response = await fetch(`${{API_BASE_URL}}/health`);
                if (response.ok) {{
                    console.log('API is available');
                }} else {{
                    console.warn('API health check failed:', response.status);
                }}
            }} catch (error) {{
                console.error('API health check error:', error);
                showStatus('Предупреждение: не удалось подключиться к серверу', 'error');
            }}
        }}
        
        // Автоматически предлагаем сканировать QR при открытии WebApp
        if (tg.platform !== 'unknown') {{
            // Небольшая задержка для лучшего UX
            setTimeout(() => {{
                const firstTime = !localStorage.getItem('webapp_opened');
                if (firstTime) {{
                    localStorage.setItem('webapp_opened', 'true');
                    showStatus('Нажмите "Сканировать QR-код" для начала работы', 'loading');
                }}
                checkAPI();
            }}, 500);
        }} else {{
            checkAPI();
        }}
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
