#!/bin/bash

# SINPE Banking System Startup Script

echo "🏦 SINPE Banking System - Python Implementation"
echo "=============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies."
        exit 1
    fi
    echo "✅ Dependencies installed successfully."
fi

# Create database directory if it doesn't exist
mkdir -p database

# Run the application
echo "🚀 Starting SINPE Banking System..."
echo ""
echo "Features:"
echo "  • Terminal UI with rich interface"
echo "  • REST API server on http://127.0.0.1:5000"
echo "  • SQLite database with sample data"
echo "  • SINPE transfer simulation"
echo "  • User and account management"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

python3 main.py

# Deactivate virtual environment when done
deactivate