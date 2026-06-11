FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 8000

# Try to initialize database (non-blocking), then start app
CMD ["sh", "-c", "python init_railway.py 2>&1 || true; gunicorn -w 4 -b 0.0.0.0:8000 app:app"]
