FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY start_server.py ./start_server.py

ENV PYTHONUNBUFFERED=1

# Railway will set PORT automatically
EXPOSE 8000

CMD ["python", "start_server.py"]
