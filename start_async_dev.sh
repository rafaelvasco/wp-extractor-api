#!/bin/bash

# WordPress Extractor API - Async Development Startup Script
# This script starts all components needed for async processing

echo "Starting WordPress Extractor API with async support..."

# Check if Redis is running
if ! command -v redis-server &> /dev/null; then
    echo "Error: Redis is not installed. Please install Redis first."
    echo "On macOS: brew install redis"
    echo "On Ubuntu: sudo apt-get install redis-server"
    exit 1
fi

# Start Redis in background if not running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
    sleep 2
fi

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Warning: No virtual environment detected. Consider activating your venv first."
fi

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A celery_app worker --loglevel=info --concurrency=2 &
CELERY_PID=$!

# Start Flower monitoring in background
echo "Starting Flower monitoring..."
celery -A celery_app flower --port=5555 &
FLOWER_PID=$!

# Wait a moment for services to start
sleep 3

# Start Flask app
echo "Starting Flask application..."
echo ""
echo "Services running:"
echo "- Flask API: http://localhost:5000"
echo "- Flower monitoring: http://localhost:5555"
echo "- Redis: localhost:6379"
echo ""
echo "API Endpoints:"
echo "- Health check: GET http://localhost:5000/health"
echo "- Sync extraction: POST http://localhost:5000/extract"
echo "- Async extraction: POST http://localhost:5000/extract/async"
echo "- Task status: GET http://localhost:5000/extract/status/<task_id>"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $CELERY_PID 2>/dev/null
    kill $FLOWER_PID 2>/dev/null
    echo "Services stopped."
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Start Flask app (this will block)
python main.py

# If we get here, Flask app stopped, so cleanup
cleanup