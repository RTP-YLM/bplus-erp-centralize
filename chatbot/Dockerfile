FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY chatbot/ ./chatbot/

# NOTE: Do NOT copy .env - Railway will provide environment variables
# If running locally, ensure .env exists in the parent directory

# Expose port
EXPOSE 8000

# Run webhook server
CMD ["python", "-m", "uvicorn", "chatbot.webhook:app", "--host", "0.0.0.0", "--port", "8000"]
