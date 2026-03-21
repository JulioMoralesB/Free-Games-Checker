# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Build argument for locale
ARG LOCALE=es_ES.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends locales && \
    LOCALE_ESCAPED="$(printf '%s\n' "$LOCALE" | sed 's/[.[\*^$\/]/\\&/g')" && \
    sed -i "/^# *${LOCALE_ESCAPED}[[:space:]]/s/^# *//" /etc/locale.gen && \
    grep -Eq "^[[:space:]]*${LOCALE_ESCAPED}[[:space:]]" /etc/locale.gen && \
    locale-gen && rm -rf /var/lib/apt/lists/*

# Create directories for logs and data
RUN mkdir -p /mnt/logs /mnt/data

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Run the application
CMD ["python", "main.py"]