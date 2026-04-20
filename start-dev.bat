@echo off
REM SmartQuiz Agent - Development bootstrap for Windows.
REM Starts FastAPI backend + Next.js frontend with sensible defaults.

setlocal EnableDelayedExpansion

echo.
echo ========================================
echo  SmartQuiz Agent - Full Stack Startup
echo ========================================
echo.

REM Ensure script runs from repository root.
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if Node is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ and try again
    pause
    exit /b 1
)

echo [OK] Python: 
python --version

echo [OK] Node.js: 
node --version

REM Prefer local virtual environment if present.
set "PYTHON_CMD=python"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
)

echo.
echo [SETUP] Installing backend dependencies if needed...
%PYTHON_CMD% -m pip install -r requirements.txt

echo [SETUP] Installing frontend dependencies if needed...
if not exist "frontend\node_modules" (
    pushd frontend
    npm install
    popd
)

echo.
echo Starting SmartQuiz Agent...
echo.

REM Start FastAPI backend in new window
echo [1/2] Starting FastAPI Backend on http://localhost:8000
start "SmartQuiz - FastAPI Backend" cmd /k "%PYTHON_CMD% api_server.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak

REM Start Next.js frontend in new window
echo [2/2] Starting Next.js Frontend on http://localhost:3000
start "SmartQuiz - Next.js Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo  Both servers are starting!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press CTRL+C in each window to stop the servers
echo.
pause
