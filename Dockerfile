FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make sure scripts are executable
RUN chmod +x scripts/*.sh || true

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port for web interface (if needed in the future)
EXPOSE 5000

# Default command
CMD ["python", "src/main.py", "--interactive"]
