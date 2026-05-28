#!/bin/bash

# PDF Assistant Quick Start Script
# This script sets up and runs both backend and frontend

set -e

echo "🚀 PDF Document Assistant - Quick Start"
echo "========================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Tesseract is installed
echo -e "${BLUE}Checking Tesseract OCR...${NC}"
if ! command -v tesseract &> /dev/null; then
    echo -e "${YELLOW}⚠️  Tesseract OCR not found${NC}"
    echo "Install it with:"
    echo "  macOS: brew install tesseract"
    echo "  Ubuntu: sudo apt-get install tesseract-ocr"
    echo "  Windows: https://github.com/UB-Mannheim/tesseract/wiki"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Tesseract found${NC}"
fi

# Backend Setup
echo -e "\n${BLUE}Setting up Backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    cp .env.example .env
    echo "Created .env file. Please edit it with your API key:"
    echo "  GEMINI_API_KEY=your_key_here"
    echo "  or"
    echo "  OPENAI_API_KEY=your_key_here"
    read -p "Press Enter after updating .env..."
fi

# Start backend in background
echo -e "${GREEN}✓ Backend ready${NC}"
echo "Starting backend on http://localhost:8000..."
python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Frontend Setup
echo -e "\n${BLUE}Setting up Frontend...${NC}"
cd ../frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install -q
fi

# Check for .env.local file
if [ ! -f ".env.local" ]; then
    cp .env.example .env.local
    echo "Created .env.local file"
fi

echo -e "${GREEN}✓ Frontend ready${NC}"
echo "Starting frontend on http://localhost:3000..."

# Start frontend
npm run dev &
FRONTEND_PID=$!

# Wait a bit for frontend to start
sleep 3

echo -e "\n${GREEN}✓ All services started!${NC}"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔌 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
