# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends locales && \
    rm -rf /var/lib/apt/lists/*

# Create directories for logs and data
RUN mkdir -p /mnt/logs /mnt/data

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Run the application
ENTRYPOINT ["/app/entrypoint.sh"]