@echo off
echo 🔍 Video Art Masterpiece - Docker Logs Viewer
echo ===============================================
echo.

echo 📊 Container Status:
docker compose ps
echo.

echo 🔍 Choose logs to view:
echo [1] All services
echo [2] Backend only
echo [3] Frontend only  
echo [4] MongoDB only
echo [5] Live tail (all services)
echo [6] Exit
echo.

set /p choice="Enter choice (1-6): "

if "%choice%"=="1" (
    echo.
    echo 📋 All service logs:
    docker compose logs --tail=50
) else if "%choice%"=="2" (
    echo.
    echo 🔧 Backend logs:
    docker compose logs --tail=50 backend
) else if "%choice%"=="3" (
    echo.
    echo 🌐 Frontend logs:
    docker compose logs --tail=50 frontend
) else if "%choice%"=="4" (
    echo.
    echo 🗄️ MongoDB logs:
    docker compose logs --tail=50 mongodb
) else if "%choice%"=="5" (
    echo.
    echo 📡 Live logs (Press Ctrl+C to exit):
    docker compose logs -f
) else if "%choice%"=="6" (
    echo.
    echo 👋 Goodbye!
    exit /b 0
) else (
    echo.
    echo ❌ Invalid choice!
)

echo.
pause