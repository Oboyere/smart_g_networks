FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 8000

# Initialize database and start app
CMD ["sh", "-c", "python init_railway.py; gunicorn -w 4 -b 0.0.0.0:8000 app:app"]
