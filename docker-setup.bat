@echo off
echo 🐳 Video Art Masterpiece - Docker Setup
echo =========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found! Please install Docker Desktop first.
    echo 📥 Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker compose version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose not found! Please update Docker Desktop.
    pause
    exit /b 1
)

echo ✅ Docker found: 
docker --version
echo.

echo 🧹 Cleaning up any existing containers...
docker compose down -v 2>nul

echo 📦 Building and starting Video Art Masterpiece...
echo This may take 5-10 minutes for first-time setup...
echo.

docker compose up --build -d

if errorlevel 1 (
    echo ❌ Failed to start containers!
    echo.
    echo Checking container status...
    docker compose ps
    echo.
    echo Checking logs...
    docker compose logs --tail=20
    pause
    exit /b 1
)

echo.
echo 🎉 Video Art Masterpiece is starting up!
echo.
echo 📊 Container status:
docker compose ps

echo.
echo 🌐 Application URLs:
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8001
echo   Database: mongodb://localhost:27017
echo.

echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo 🔍 Health check:
curl -s http://localhost:8001/api/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Backend not ready yet, please wait a moment...
) else (
    echo ✅ Backend is healthy!
)

curl -s http://localhost:3000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Frontend not ready yet, please wait a moment...
) else (
    echo ✅ Frontend is healthy!
)

echo.
echo 🎨 Ready to create video masterpieces!
echo Open http://localhost:3000 in your browser
echo.

echo 📋 Useful Docker commands:
echo   View logs: docker compose logs -f
echo   Stop: docker compose down
echo   Restart: docker compose restart
echo   Status: docker compose ps
echo.

pause