#!/bin/bash
# DockerMonitor - Quick start script for Linux/Mac

set -e

echo "DockerMonitor - Docker Container Monitoring"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "Virtual environment created successfully."
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import textual" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "Dependencies installed successfully."
fi

# Check if configuration exists
if [ ! -f "config/hosts.yaml" ]; then
    echo ""
    echo "Warning: config/hosts.yaml not found!"
    echo "Please copy config/hosts.yaml.example to config/hosts.yaml"
    echo "and configure your jump host and target servers."
    echo ""
    exit 1
fi

# Run the application
echo ""
echo "Starting DockerMonitor TUI..."
echo ""
python -m src.main tui

deactivate
