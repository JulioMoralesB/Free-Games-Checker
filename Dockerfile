# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install tzdata package for timezone data
RUN apt-get update && apt-get install -y locales && sed -i '/es_ES.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

# Set the timezone environment variable to Mexico City
ENV TZ=America/Mexico_City
ENV LANG es_ES.UTF-8
ENV LANGUAGE es_ES:es
ENV LC_ALL es_ES.UTF-8

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