FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY chatbot/ ./chatbot/

# Do NOT copy .env - use Railway environment variables instead

# Expose port (Railway sets PORT env var)
EXPOSE ${PORT:-8000}

# Run webhook server (use PORT env var if set, default 8000)
CMD ["sh", "-c", "python -m uvicorn chatbot.webhook:app --host 0.0.0.0 --port ${PORT:-8000}"]
