#!/bin/bash

# FDA Oncology Copilot Word Add-in Setup Script

echo "Setting up FDA Oncology Copilot Word Add-in..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "Error: pip is required but not installed."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo "Please edit the .env file to add your OpenAI API key."
    echo "Press Enter to continue after editing the file..."
    read
fi

# Check if indices are built
if [ ! -d "data/indices" ] || [ -z "$(ls -A data/indices 2>/dev/null)" ]; then
    echo "Building vector indices..."
    python scripts/build_indices.py
fi

# Start the Word add-in backend service
echo "Starting FDA Oncology Copilot Word Add-in backend service..."
echo "Please follow these steps to install the add-in in Word:"
echo "1. Open Microsoft Word"
echo "2. Go to 'Insert' > 'Get Add-ins' > 'Manage My Add-ins' > 'Upload My Add-in'"
echo "3. Select the 'word_addin/manifest.xml' file"
echo "4. Click 'Install'"
echo ""
echo "Starting backend service..."
python word_addin/run_server.py
