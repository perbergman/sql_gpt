#!/bin/bash
# Start the SQL-GPT application with Docker Compose

# Verify OPENAI_API_KEY is available
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: OPENAI_API_KEY environment variable not found"
    echo "Please make sure to run this script from a shell where OPENAI_API_KEY is set"
    echo "For example: OPENAI_API_KEY=your_key_here ./scripts/start.sh"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH"
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo "ERROR: Docker Compose is not installed or not in PATH"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Stop any existing containers to avoid conflicts
echo "Stopping any existing SQL-GPT containers..."
$DOCKER_COMPOSE_CMD down 2>/dev/null || true

# Start the containers
echo "Starting SQL-GPT with Docker Compose..."
$DOCKER_COMPOSE_CMD up -d

echo "SQL-GPT is now running!"
echo "Web interface available at: http://localhost:5001"
echo "To access the interactive mode: $DOCKER_COMPOSE_CMD exec app python src/main.py --interactive"
echo "To stop: ./scripts/stop.sh"
