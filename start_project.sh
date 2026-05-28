#!/bin/bash

echo "🚀 Starting PDF Document Assistant with Chroma Cloud"
echo "=================================================="

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "❌ backend/.env not found"
    echo "Please create backend/.env with your Chroma Cloud credentials"
    exit 1
fi

# Initialize Chroma Cloud collection
echo ""
echo "📦 Initializing Chroma Cloud..."
cd backend
python init_chroma.py

if [ $? -ne 0 ]; then
    echo "❌ Failed to initialize Chroma Cloud"
    exit 1
fi

# Install dependencies if needed
echo ""
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

# Start backend
echo ""
echo "🔌 Starting backend on http://localhost:8000..."
python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo ""
echo "🎨 Starting frontend on http://localhost:3000..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Services started!"
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
