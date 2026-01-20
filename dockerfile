# Dockerfile đơn giản
FROM python:3.11-alpine

WORKDIR /app

# Install dependencies
RUN apk add --no-cache sqlite-libs

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy main.py
COPY main.py .

# Run as non-root
RUN adduser -D appuser
USER appuser

# Start bot
CMD ["python", "main.py"]