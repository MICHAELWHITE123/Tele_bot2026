from contextlib import asynccontextmanager
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from pydantic import BaseModel

from app.google_sheets import get_sheets_client
from app.bot import start_polling


bot_task = None
webapp_html_bytes = None
info_html_bytes = None
history_html_bytes = None
checked_html_bytes = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_task, webapp_html_bytes, info_html_bytes, history_html_bytes, checked_html_bytes
    
    html_path = Path(__file__).parent / "webapp.html"
    with open(html_path, "rb") as f:
        webapp_html_bytes = f.read()
    
    info_path = Path(__file__).parent / "info.html"
    with open(info_path, "rb") as f:
        info_html_bytes = f.read()
    
    history_path = Path(__file__).parent / "history.html"
    with open(history_path, "rb") as f:
        history_html_bytes = f.read()
    
    checked_path = Path(__file__).parent / "checked.html"
    with open(checked_path, "rb") as f:
        checked_html_bytes = f.read()
    
    bot_task = asyncio.create_task(start_polling())
    
    yield
    
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Warehouse Bot WebApp API",
    description="REST API for managing warehouse items and labels in Google Sheets",
    version="1.0.0",
    lifespan=lifespan
)


class CheckRequest(BaseModel):
    inventory_id: str


class CheckResponse(BaseModel):
    status: str
    inventory_id: str


class UpdateInventoryNumberRequest(BaseModel):
    inventory_id: str
    inventory_number: str


@app.get("/")
async def root():
    return RedirectResponse(url="/webapp")


@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={}, status_code=204)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/items", response_model=list[dict])
async def get_all_items():
    try:
        client = get_sheets_client()
        items = client.get_all_items()
        return items
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": "internal server error"}
        )


@app.get("/items/{inventory_id}", response_model=dict)
async def get_item_by_id(inventory_id: str):
    try:
        client = get_sheets_client()
        item = client.find_item_by_inventory_id(inventory_id)
        
        if item is None:
            return JSONResponse(
                status_code=404,
                content={"error": "inventory_id not found"}
            )
        
        return item
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": "internal server error"}
        )


@app.post("/items/check", response_model=CheckResponse)
async def check_item(request: CheckRequest):
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
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": "internal server error"}
        )


@app.post("/items/uncheck", response_model=CheckResponse)
async def uncheck_item(request: CheckRequest):
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
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": "internal server error"}
        )


@app.get("/webapp", response_class=HTMLResponse)
async def webapp():
    return HTMLResponse(content=webapp_html_bytes.decode('utf-8'))


@app.post("/items/update-inventory-number", response_model=CheckResponse)
async def update_inventory_number(request: UpdateInventoryNumberRequest):
    try:
        client = get_sheets_client()
        item = client.find_item_by_inventory_id(request.inventory_id)
        
        if item is None:
            return JSONResponse(
                status_code=404,
                content={"error": "inventory_id not found"}
            )
        
        client.update_column_z(item["row_index"], request.inventory_number)
        
        return CheckResponse(
            status="ok",
            inventory_id=request.inventory_id
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": "internal server error"}
        )


@app.get("/info", response_class=HTMLResponse)
async def info():
    return HTMLResponse(content=info_html_bytes.decode('utf-8'))


@app.get("/history", response_class=HTMLResponse)
async def history():
    return HTMLResponse(content=history_html_bytes.decode('utf-8'))


@app.get("/checked", response_class=HTMLResponse)
async def checked():
    return HTMLResponse(content=checked_html_bytes.decode('utf-8'))
