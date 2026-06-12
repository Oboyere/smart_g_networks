FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use port from environment variable or default to 8000
ENV PORT=8000

# Try to initialize database (non-blocking), then start app with proper port
CMD ["sh", "-c", "python init_railway.py 2>&1 || true; gunicorn -w 4 -b 0.0.0.0:${PORT} app:app"]
