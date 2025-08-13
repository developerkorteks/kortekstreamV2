FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --timeout=300 --retries=3 -r requirements.txt

# Copy project
COPY . .

# Create directories
RUN mkdir -p /app/logs /app/media /app/static

# Set permissions
RUN chmod +x /app/entrypoint.sh || true

# Expose port
EXPOSE 9111

# Run entrypoint
CMD ["/app/entrypoint.sh"]