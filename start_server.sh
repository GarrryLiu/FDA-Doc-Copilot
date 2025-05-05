#!/bin/bash

# Display a message
echo "Starting FDA Oncology Copilot with automatic index rebuilding..."

# Clean up old indices
echo "Cleaning up old indices..."
rm -rf data/indices/*

# Rebuild all indices
echo "Rebuilding indices..."
python scripts/build_indices.py

# Start the server
echo "Starting server..."
python word_addin/run_server.py
