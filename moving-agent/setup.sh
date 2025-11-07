#!/bin/bash

echo "🚚 Setting up AI Moving Agent Demo..."

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Install system dependencies (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Installing Linux system dependencies..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y \
            libatk1.0-0 \
            libatk-bridge2.0-0 \
            libcups2 \
            libdrm2 \
            libxkbcommon0 \
            libatspi2.0-0 \
            libxcomposite1 \
            libxdamage1 \
            libxfixes3 \
            libgbm1 \
            libpango-1.0-0
    else
        echo "⚠️ apt-get not found. Please install system dependencies manually."
    fi
fi

echo "✅ Setup complete!"
echo ""
echo "🎬 To run the demo:"
echo "   python demo.py          # Live browser demo"
echo "   python demo_simple.py   # Simulation demo (no dependencies)"