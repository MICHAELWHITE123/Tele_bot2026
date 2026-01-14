#!/usr/bin/env python3
"""Start script for Railway that runs both FastAPI server and Telegram bot."""
import os
import sys
import asyncio
import threading
import uvicorn

def get_port():
    """Get PORT from environment and validate it."""
    port_str = os.getenv("PORT", "8000")
    
    try:
        port = int(port_str)
        if 1 <= port <= 65535:
            return port
        else:
            print(f"Warning: PORT {port} out of range, using 8000", file=sys.stderr)
            return 8000
    except (ValueError, TypeError):
        print(f"Warning: Invalid PORT '{port_str}', using 8000", file=sys.stderr)
        return 8000


def run_fastapi(port: int):
    """Run FastAPI server in a separate thread."""
    from app.main import app
    
    print(f"Starting FastAPI server on port {port}", file=sys.stderr)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


async def run_bot():
    """Run Telegram bot in polling mode."""
    from app.bot import start_polling
    
    print("Starting Telegram bot...", file=sys.stderr)
    await start_polling()


if __name__ == "__main__":
    port = get_port()
    
    # Start FastAPI in a separate daemon thread
    fastapi_thread = threading.Thread(
        target=run_fastapi,
        args=(port,),
        daemon=True
    )
    fastapi_thread.start()
    
    # Wait a moment for FastAPI to start
    import time
    time.sleep(2)
    
    # Run bot in main thread
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("Shutting down...", file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
