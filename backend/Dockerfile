FROM mcr.microsoft.com/playwright/python:v1.61.0-noble
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
# One worker so a single APScheduler instance runs; threads handle concurrent reads.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "300", "app:create_app()"]
