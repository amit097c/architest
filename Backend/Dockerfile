FROM python:3.12-slim AS base

# Set working directory
WORKDIR /app

# Development stage
FROM base AS development
# Copy requirements first
COPY requirements.txt .
# Install system dependencies and Python dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install pytest \
    && playwright install --with-deps chromium \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .
EXPOSE 8001
CMD ["python", "-m", "uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

# Production stage - more optimized
FROM base AS production
# Copy requirements first
COPY requirements.txt .

# Add non-root user first
RUN adduser --disabled-password --gecos "" appuser

# Install only runtime dependencies, install deps, and cleanup in a single layer to reduce size
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install pytest \
    && mkdir -p /home/appuser/.cache \
    && PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright playwright install --with-deps chromium \
    && chown -R appuser:appuser /home/appuser/.cache \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && find /usr/local -type d -name '__pycache__' -exec rm -rf {} +

# Copy application code
COPY . .

# Change ownership to the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8001

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/ || exit 1

CMD ["python", "-m", "uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8001"] 