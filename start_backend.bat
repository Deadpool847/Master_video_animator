@echo off
echo 🚀 Starting Video Art Masterpiece Backend...
echo.

REM Check if virtual environment exists
if not exist venv\Scripts\activate.bat (
    echo ❌ Virtual environment not found!
    echo Please run setup_windows.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
echo ✅ Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if MongoDB is running
echo 🗄️ Checking MongoDB connection...
net start | findstr "MongoDB" >nul
if errorlevel 1 (
    echo ⚠️ MongoDB service might not be running.
    echo Starting MongoDB service...
    net start MongoDB 2>nul
    if errorlevel 1 (
        echo ❌ Could not start MongoDB service.
        echo Please start MongoDB manually or check installation.
        echo.
    )
)

REM Start backend server
echo 🎨 Starting FastAPI server on http://localhost:8001...
cd backend
python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

REM Keep window open on error
if errorlevel 1 (
    echo.
    echo ❌ Backend failed to start. Check the error messages above.
    pause
)