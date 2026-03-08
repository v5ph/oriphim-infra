# Dockerfile for Oriphim Watcher Protocol

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    sqlite3 \
    libsqlcipher-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY app/ ./app/
COPY scripts/ ./scripts/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create data and logs directories
RUN mkdir -p /app/data /app/logs

# Initialize database on first run
RUN python -c "from app.core.storage import init_db; from app.core.onboarding import init_onboarding_db; init_db(); init_onboarding_db()"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/v2/health || exit 1

# Run server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
