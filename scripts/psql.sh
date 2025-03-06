#!/bin/bash
# Connect to PostgreSQL database

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

echo "Connecting to PostgreSQL database..."
$DOCKER_COMPOSE_CMD exec db psql -U postgres -d sql_gpt

echo "PostgreSQL connection closed."
