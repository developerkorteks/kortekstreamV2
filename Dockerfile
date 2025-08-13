FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=kortekstream.settings.production

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat-traditional \
    curl \
    libmemcached-dev \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script first and make it executable
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh && \
    # Ensure script has Unix line endings
    sed -i 's/\r$//' /app/entrypoint.sh

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/media /app/static

# Expose port (using non-standard port as requested)
EXPOSE 9326

# Set entrypoint
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:9326", "--workers", "3", "kortekstream.wsgi:application"]