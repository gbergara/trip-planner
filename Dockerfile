FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copy application code
COPY app/ ./app/

# Compile .po to .mo and sync mtimes for translation files
RUN apt-get update && apt-get install -y gettext && \
    find app/locales -name "messages.po" -exec sh -c 'msgfmt "$0" -o "${0%.po}.mo" && touch -r "$0" "${0%.po}.mo"' {} \; && \
    apt-get remove -y gettext && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy tests and configuration
COPY tests/ ./tests/
COPY pytest.ini ./

# Copy Alembic configuration and migrations
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Create directory for SQLite database
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
