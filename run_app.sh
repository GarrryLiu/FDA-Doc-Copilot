#!/bin/bash

# FDA Oncology Copilot Runner Script

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    if [ -f .env.template ]; then
        echo "Warning: .env file not found. Creating from template..."
        cp .env.template .env
        echo "Please edit .env to add your OpenAI API key."
        exit 1
    else
        echo "Error: Neither .env nor .env.template found."
        exit 1
    fi
fi

# Check if requirements are installed
echo "Checking dependencies..."
if ! python3 -c "import streamlit, openai, faiss, langchain" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the application
echo "Starting FDA Oncology Copilot..."
python3 run.py
