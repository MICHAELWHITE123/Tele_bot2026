#!/bin/sh
# Start script that ensures PORT is a valid integer

# Get PORT from environment, default to 8000
PORT=${PORT:-8000}

# Convert to integer (remove any non-numeric characters)
PORT=$(echo "$PORT" | sed 's/[^0-9]//g')

# If empty or invalid, use default
if [ -z "$PORT" ] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    PORT=8000
fi

# Start uvicorn with validated PORT
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
