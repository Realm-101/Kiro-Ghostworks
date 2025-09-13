# Multi-stage build for Celery worker service
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY services/worker/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/worker/ .
COPY packages/shared/ /shared/

# Create logs directory
RUN mkdir -p logs && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Run the Celery worker
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info", "--concurrency=4"]