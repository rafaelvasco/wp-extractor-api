# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (only for Flask API, not for workers)
EXPOSE 5000

# Conditional health check based on service type
# Workers don't need HTTP health checks
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD if [ "$SERVICE_TYPE" = "worker" ]; then \
            celery -A celery_app inspect ping -d celery@$HOSTNAME || exit 1; \
        else \
            curl -f http://localhost:5000/health || exit 1; \
        fi

# Conditional command based on SERVICE_TYPE environment variable
# If SERVICE_TYPE=worker, start Celery worker
# Otherwise, start Gunicorn (Flask API)
CMD ["sh", "-c", "if [ \"$SERVICE_TYPE\" = \"worker\" ]; then celery -A celery_app worker --loglevel=info --concurrency=2 --queues=celery,extraction; else gunicorn --config gunicorn.conf.py main:app; fi"]