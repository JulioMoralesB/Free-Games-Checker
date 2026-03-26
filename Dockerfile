# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies and create a non-root user in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
        gosu \
        locales \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --no-create-home --shell /bin/false appuser \
    && mkdir -p /mnt/logs /mnt/data \
    && chown appuser:appuser /mnt/logs /mnt/data

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make scripts executable; application code stays root-owned (read-only for appuser)
RUN chmod +x /app/entrypoint.sh /app/healthcheck.sh

# The entrypoint runs as root to support locale-gen; gosu drops to appuser for the Python process.
# Health check: confirm the main Python process is running
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/healthcheck.sh

# Run the application
ENTRYPOINT ["/app/entrypoint.sh"]