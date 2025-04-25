FROM python:3.12-slim AS base

# Set working directory
WORKDIR /app

# Development stage
FROM base AS development
# Copy requirements first
COPY requirements.txt .

# Install dependencies in single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    curl \
    unzip \
    build-essential \
    default-jdk \
    && pip install --no-cache-dir -r requirements.txt uvicorn \
    && playwright install --with-deps chromium \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \ 
    && apt-get install -y nodejs
# Copy application code
COPY . .

# Install Playwright + Newman in javascript_utils folder
WORKDIR /app/agent/utils/javascript_utils
RUN npm init -y \ 
    && npm install -D @playwright/test \
    && npm install newman \
    && npx playwright install

# Java Utilities setup
WORKDIR /tmp
RUN curl -L -o selenium-java-4.zip https://github.com/SeleniumHQ/selenium/releases/download/selenium-4.31.0/selenium-java-4.31.0.zip \ 
    && unzip selenium-java-4.zip -d /app/agent/utils/java_utils \
    && curl -L -o chromedriver-mac-x64.zip https://storage.googleapis.com/chrome-for-testing-public/135.0.7049.114/mac-x64/chromedriver-mac-x64.zip \
    && unzip chromedriver-mac-x64.zip -d /app/agent/utils/java_utils \
    && rm selenium-java-4.zip chromedriver-mac-x64.zip

# Go back to root app dir
WORKDIR /app
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage - more optimized
FROM base AS production
# Copy requirements first
COPY requirements.txt .

# Add non-root user first
RUN adduser --disabled-password --gecos "" appuser

# Install only runtime dependencies, install deps, and cleanup in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    curl \
    unzip \
    default-jdk \
    && pip install --no-cache-dir -r requirements.txt uvicorn \
    && mkdir -p /home/appuser/.cache \
    && PLAYWRIGHT_BROWSERS_PATH=/home/appuser/.cache/ms-playwright playwright install --with-deps chromium \
    && chown -R appuser:appuser /home/appuser/.cache \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && find /usr/local -type d -name '__pycache__' -exec rm -rf {} +

# Install Node.js and JS tools
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \ 
    && apt-get install -y nodejs \
    && cd /app/agent/utils/javascript_utils \
    && npm init -y \
    && npm install -D @playwright/test \
    && npm install newman \
    && npx playwright install \
    && cd /app

# Install Java utils
RUN curl -L -o selenium-java-4.zip https://github.com/SeleniumHQ/selenium/releases/download/selenium-4.31.0/selenium-java-4.31.0.zip \ 
    && unzip selenium-java-4.zip -d /app/agent/utils/java_utils \
    && curl -L -o chromedriver-mac-x64.zip https://storage.googleapis.com/chrome-for-testing-public/135.0.7049.114/mac-x64/chromedriver-mac-x64.zip \
    && unzip chromedriver-mac-x64.zip -d /app/agent/utils/java_utils \
    && rm selenium-java-4.zip chromedriver-mac-x64.zip

# Copy application code
COPY . .

# Change ownership to the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"] 