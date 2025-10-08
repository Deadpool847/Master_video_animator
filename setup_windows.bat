@echo off
echo 🎨 Video Art Masterpiece - Windows Setup
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.11+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found! Please install Node.js 18+ first.
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment!
    pause
    exit /b 1
)

REM Activate virtual environment
echo ✅ Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

REM Install backend dependencies
echo 🐍 Installing Python dependencies...
cd backend
pip install -r requirements_windows.txt
if errorlevel 1 (
    echo ⚠️ Some packages failed. Trying individual installation...
    pip install fastapi uvicorn python-multipart aiofiles motor python-dotenv
    pip install opencv-python-headless numpy pillow requests
)

REM Return to root and install frontend
cd ..
echo ⚛️ Installing Node.js dependencies...
cd frontend

REM Try yarn first, then npm
yarn --version >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing with npm...
    npm install
) else (
    echo 📦 Installing with yarn...
    yarn install
)

cd ..

echo.
echo 🎉 Setup complete!
echo.
echo Next steps:
echo 1. Ensure MongoDB is running (net start MongoDB)
echo 2. Run: start_backend.bat
echo 3. Run: start_frontend.bat (in another terminal)
echo 4. Open http://localhost:3000 in your browser
echo.
echo For FFmpeg installation, run:
echo   choco install ffmpeg
echo Or download manually from: https://www.gyan.dev/ffmpeg/builds/
echo.
pause