# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install tzdata and generate all UTF-8 locales so any LOCALE value works at runtime
RUN apt-get update && apt-get install -y locales tzdata && \
    sed -i 's/^# \(.*\.UTF-8\)/\1/' /etc/locale.gen && \
    locale-gen && \
    rm -rf /var/lib/apt/lists/*

# Default timezone and locale – override at runtime via environment variables:
#   docker run -e TZ=Europe/London -e LANG=en_GB.UTF-8 ...
ENV TZ=UTC
ENV LANG=C.UTF-8
ENV LANGUAGE=C.UTF-8
ENV LC_ALL=C.UTF-8

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