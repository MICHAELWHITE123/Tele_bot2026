from fastapi import FastAPI

from app.config import config

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}
