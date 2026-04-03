# Use the official Python image from the Docker Hub
# Stage 1: Build the React/TypeScript dashboard
FROM node:20-slim AS dashboard-builder
WORKDIR /app/dashboard
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim

# Build-time locale selection (default en_US.UTF-8).
# To use a different locale, pass --build-arg LOCALE=<your_locale> and rebuild.
ARG LOCALE=en_US.UTF-8

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies, generate only the selected locale, and create a non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
        locales \
    && printf '%s UTF-8\n' "${LOCALE}" > /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1000 appuser \
    && useradd --system --no-create-home --shell /bin/false --uid 1000 --gid 1000 appuser
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

# Copy the pre-built dashboard static files from the builder stage
COPY --from=dashboard-builder /app/dashboard/dist ./dashboard/dist

# Create writable directories for appuser and make healthcheck executable.
# NOTE: /mnt/logs and /mnt/data are typically bind-mounted at runtime (see compose.yaml).
# Ensure the host source directories are owned by the UID/GID of appuser in the container.
RUN mkdir -p /mnt/logs /mnt/data /app/data \
    && chown appuser:appuser /mnt/logs /mnt/data /app/data \
    && chmod +x /app/healthcheck.sh

# Switch to non-root user for all subsequent instructions and runtime
USER appuser

# Expose the REST API port (default 8000, configurable via API_PORT env var)
EXPOSE 8000

# Health check: confirm the main Python process is running
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/healthcheck.sh

# Run the application
CMD ["python", "main.py"]