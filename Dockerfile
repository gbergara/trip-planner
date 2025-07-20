
# --- Build stage ---
FROM python:3.11-alpine as builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev gettext

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Compile .po to .mo and sync mtimes for translation files
RUN find app/locales -name "messages.po" -exec sh -c 'msgfmt "$0" -o "${0%.po}.mo" && touch -r "$0" "${0%.po}.mo"' {} \;

# Copy Alembic and test files for migration/test images
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY tests/ ./tests/
COPY pytest.ini ./

# --- Final stage ---
FROM python:3.11-alpine

# Install runtime dependencies
RUN apk add --no-cache libffi gettext

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy installed Python packages from builder
ENV PATH="/root/.local/bin:$PATH"
COPY --from=builder /root/.local /root/.local

# Copy application code and assets
COPY --from=builder /app/app /app/app
COPY --from=builder /app/alembic.ini /app/alembic.ini
COPY --from=builder /app/alembic /app/alembic
COPY --from=builder /app/tests /app/tests
COPY --from=builder /app/pytest.ini /app/pytest.ini

# Create directory for SQLite database
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
