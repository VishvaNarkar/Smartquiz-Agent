#!/bin/bash
# SmartQuiz Agent - Development bootstrap for macOS/Linux.

set -e

# Ensure script runs from repository root.
cd "$(dirname "$0")"

echo ""
echo "========================================"
echo "  SmartQuiz Agent - Full Stack Startup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed or not in PATH"
    echo "Please install Node.js 18+ and try again"
    exit 1
fi

echo "[OK] Python:"
python3 --version

echo "[OK] Node.js:"
node --version

# Prefer local virtual environment if available.
PYTHON_CMD="python3"
if [ -x ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
fi

echo ""
echo "[SETUP] Installing backend dependencies if needed..."
"$PYTHON_CMD" -m pip install -r requirements.txt

echo "[SETUP] Installing frontend dependencies if needed..."
if [ ! -d "frontend/node_modules" ]; then
    (cd frontend && npm install)
fi

echo ""
echo "Starting SmartQuiz Agent..."
echo ""

# Start FastAPI backend
echo "[1/2] Starting FastAPI Backend on http://localhost:8000"
"$PYTHON_CMD" api_server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start Next.js frontend
echo "[2/2] Starting Next.js Frontend on http://localhost:3000"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  Both servers are starting!"
echo "========================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop both servers"
echo ""

# Ensure both child processes stop on interrupt.
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" INT TERM EXIT

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
