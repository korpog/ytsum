# Use the official Python image with version 3.9 (or specify your preferred version)
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt before other files for efficient caching
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose port 5000 for the Flask app
EXPOSE 5000

# Command to run the app
CMD ["python", "app.py"]
