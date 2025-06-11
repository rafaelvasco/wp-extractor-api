#!/bin/bash

# WordPress Extractor API - Production Startup Script
# This script starts the Flask application using Gunicorn WSGI server

echo "Starting WordPress Extractor API with Gunicorn..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Warning: No virtual environment detected. Consider activating your venv first."
fi

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start Gunicorn with configuration file
echo "Starting Gunicorn server..."
gunicorn --config gunicorn.conf.py main:app

echo "Server stopped."