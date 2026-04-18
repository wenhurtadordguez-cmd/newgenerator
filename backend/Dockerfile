FROM python:3.12-slim

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Install system dependencies for Playwright (with security updates)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg2 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Set Playwright browsers path to app directory (accessible by appuser)
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.playwright

# Install Playwright browsers to shared location
RUN mkdir -p /app/.playwright && \
    playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY --chown=appuser:appuser app/ ./app/

# Ensure appuser can access browser cache
RUN chown -R appuser:appuser /app/.playwright

# Switch to non-root user
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run with strict parameters
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
