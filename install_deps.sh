#!/bin/bash

# Install script for IQ Option Gann Square 9 + Martingale Trading Bot

echo "🚀 Installing IQ Option Trading Bot dependencies..."

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 and try again."
    exit 1
fi

echo "✅ Python3 found"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Upgrade pip
echo "🔄 Upgrading pip..."
pip3 install --upgrade pip

# Install required packages
echo "📦 Installing required packages..."

# Install packages from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    echo "📄 Installing packages from requirements.txt..."
    pip3 install -r requirements.txt
else
    echo "📄 requirements.txt not found, installing packages individually..."
    pip3 install numpy
    pip3 install iqoptionapi
fi

# Verify installation
echo "🔍 Verifying installations..."

python3 -c "import numpy; print('✅ numpy version:', numpy.__version__)"
python3 -c "import iqoptionapi; print('✅ iqoptionapi installed')"
python3 -c "import asyncio; print('✅ asyncio available')"
python3 -c "import threading; print('✅ threading available')"

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "You can now run the bot with:"
echo "  python3 iqoption_gann_bot.py --mode backtest    # For backtesting"
echo "  python3 iqoption_gann_bot.py --mode live        # For live trading (requires credentials)"
echo ""