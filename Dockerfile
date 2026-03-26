# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Build-time locale selection (default es_ES.UTF-8).
# To use a different locale, pass --build-arg LOCALE=<your_locale> and rebuild.
ARG LOCALE=es_ES.UTF-8

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies, generate only the selected locale, and create a non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
        locales \
    && printf '%s UTF-8\n' "${LOCALE}" > /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --no-create-home --shell /bin/false --user-group appuser

# Bake the selected locale into the image's default runtime environment
ENV LOCALE=${LOCALE} \
    LANG=${LOCALE} \
    LANGUAGE=${LOCALE} \
    LC_ALL=${LOCALE}

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create writable directories for appuser and make healthcheck executable.
# NOTE: /mnt/logs and /mnt/data are typically bind-mounted at runtime (see compose.yaml).
# Ensure the host source directories are owned by the UID/GID of appuser in the container.
RUN mkdir -p /mnt/logs /mnt/data /app/data \
    && chown appuser:appuser /mnt/logs /mnt/data /app/data \
    && chmod +x /app/healthcheck.sh

# Switch to non-root user for all subsequent instructions and runtime
USER appuser

# Health check: confirm the main Python process is running
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/healthcheck.sh

# Run the application
CMD ["python", "main.py"]