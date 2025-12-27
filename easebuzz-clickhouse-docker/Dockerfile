# Use Python 3.10 slim base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    openssh-client && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create the /keys directory for SSH key mounting
RUN mkdir -p /keys

# Note: SSH keys are mounted at runtime via docker-compose volumes
# DO NOT copy SSH keys into the image for security reasons

# Create a script to set SSH key permissions and run the app
RUN echo '#!/bin/bash\n\
if [ -f "$SSH_KEY_PATH" ]; then\n\
    chmod 600 "$SSH_KEY_PATH"\n\
    echo "SSH key permissions set to 600"\n\
fi\n\
exec python app.py' > /entrypoint.sh && chmod +x /entrypoint.sh

# Run the application with entrypoint script
CMD ["/entrypoint.sh"]
