#!/usr/bin/env python3
"""Start script for Railway deployment that validates PORT."""
import os
import sys

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

if __name__ == "__main__":
    port = get_port()
    print(f"Starting server on port {port}", file=sys.stderr)
    
    import uvicorn
    from app.main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
