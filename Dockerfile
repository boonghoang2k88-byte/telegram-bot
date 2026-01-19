FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .

# Create necessary directories
RUN mkdir -p backups

# Run bot
CMD ["python", "main.py"]