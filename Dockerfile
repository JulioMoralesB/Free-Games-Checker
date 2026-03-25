# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install locales and create runtime directories in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends locales && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /mnt/logs /mnt/data

# Copy and install Python dependencies (cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint before the full source copy so its layer is cached
# independently of application code changes
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

# Copy the rest of the application code
COPY . .

# Run the application
ENTRYPOINT ["/app/entrypoint.sh"]