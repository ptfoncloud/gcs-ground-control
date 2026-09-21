FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system utilities needed for compiling network/serial extensions if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Cache dependency layer
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY app/ app/

# Bind both the FastAPI HTTP/WebSocket port and the MAVLink UDP port
EXPOSE 8080/tcp
EXPOSE 14550/udp

# Run FastAPI via Uvicorn bound to 0.0.0.0 inside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]