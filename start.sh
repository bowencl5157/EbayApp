#!/bin/bash
# Start script for eBay Product Research Tool (macOS/Linux)
# This script activates the virtual environment and starts the FastAPI server

# Change to the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "\033[32mStarting eBay Product Research Tool...\033[0m"
echo -e "\033[33mActivating virtual environment...\033[0m"

# Activate virtual environment
source .venv/bin/activate

# Check if port 8000 is already in use
PID=$(lsof -ti:8000 2>/dev/null)
if [ -n "$PID" ]; then
    echo -e "\033[33mPort 8000 is already in use. Stopping existing server process...\033[0m"
    kill -9 "$PID"
    sleep 1
fi

echo -e "\033[33mStarting FastAPI server...\033[0m"
echo -e "\033[36mServer will be available at http://localhost:8000\033[0m"
echo -e "\033[90mPress CTRL+C to stop the server\033[0m"
echo ""

# Start the FastAPI server
python main.py
