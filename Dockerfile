# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies, pre-generate all UTF-8 locales, and create a non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
        locales \
    && sed -i 's/^# *\(.*UTF-8\)/\1/' /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --no-create-home --shell /bin/false --user-group appuser

# Default locale; can be overridden at runtime via the LOCALE environment variable
ENV LANG=es_ES.UTF-8 \
    LANGUAGE=es_ES.UTF-8 \
    LC_ALL=es_ES.UTF-8

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create writable directories for appuser and make scripts executable.
# NOTE: /mnt/logs and /mnt/data are typically bind-mounted at runtime (see compose.yaml).
# Ensure the host source directories are owned by the UID/GID of appuser in the container.
RUN mkdir -p /mnt/logs /mnt/data /app/data \
    && chown appuser:appuser /mnt/logs /mnt/data /app/data \
    && chmod +x /app/entrypoint.sh /app/healthcheck.sh

# Switch to non-root user for all subsequent instructions and runtime
USER appuser

# Health check: confirm the main Python process is running
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/healthcheck.sh

# Run the application
ENTRYPOINT ["/app/entrypoint.sh"]