# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Create instance directory
RUN mkdir -p instance

# Set environment variables
ENV FLASK_APP=summ
ENV FLASK_ENV=production
ENV FLASK_RUN_HOST=0.0.0.0

# Expose the port
EXPOSE 5000

# Run the application
CMD ["flask", "run"]