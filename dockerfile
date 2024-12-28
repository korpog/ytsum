# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt waitress

# Copy the application
COPY . /app

# Create instance directory
RUN mkdir -p /app/instance

# Set environment variables
ENV FLASK_APP=summ
ENV FLASK_ENV=production
ENV FLASK_RUN_HOST=0.0.0.0

# Expose the port
EXPOSE 5000

# Run the application with Waitress
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "summ:create_app"]