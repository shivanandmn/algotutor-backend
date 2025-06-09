# Use Python 3.9 slim image
FROM python:3.11-slim

# Install system dependencies including Docker CLI
RUN apt-get update && \
    apt-get install -y docker.io curl ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Setup Docker permissions (handle case where group might already exist)
    getent group docker || groupadd -r docker && \
    usermod -aG docker root

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Setup Docker socket directory
RUN mkdir -p /var/run && \
    chmod 2375 /var/run

# Expose the port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
