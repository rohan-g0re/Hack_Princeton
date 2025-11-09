#!/bin/bash
# Project Setup Script for Linux/Mac

echo "========================================"
echo "Grocery Super-App Setup"
echo "========================================"
echo ""

# Create Python virtual environment
echo "[1/5] Creating Python virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment and install dependencies
echo "[2/5] Installing backend dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r server/requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "✓ Backend dependencies installed"
echo ""

# Create .env files if they don't exist
echo "[3/5] Setting up environment files..."
if [ ! -f "server/.env" ]; then
    cp server/.env.example server/.env
    echo "✓ Created server/.env from template"
    echo "⚠️  Please edit server/.env with your credentials"
else
    echo "✓ server/.env already exists"
fi
echo ""

# Create mobile folder structure
echo "[4/5] Creating mobile app structure..."
mkdir -p mobile
echo "✓ Mobile folder ready"
echo ""

echo "[5/5] Setup complete!"
echo ""
echo "========================================"
echo "Next Steps:"
echo "========================================"
echo "1. Edit server/.env with your Supabase and Gemini API keys"
echo "2. Start backend: source venv/bin/activate && cd server && python -m uvicorn server.main:app --reload"
echo "3. Run tests: source venv/bin/activate && pytest server/tests/ -v"
echo "4. Setup mobile: cd mobile && npm install"
echo ""
echo "Happy coding! 🚀"
echo ""

