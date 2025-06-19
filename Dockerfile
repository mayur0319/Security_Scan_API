# Use official Python image as base
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y \
    git \
    curl \
    openjdk-11-jre \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Nexus IQ CLI jar path (assumed already copied to /opt)
# If not present, copy it with: COPY path/to/nexus-iq-cli.jar /opt/nexus-iq-cli/nexus-iq-cli.jar
RUN mkdir -p /opt/nexus-iq-cli
# Optional: you may download it dynamically or mount via volume

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
