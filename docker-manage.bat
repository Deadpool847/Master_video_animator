@echo off
title Video Art Masterpiece - Docker Manager

:menu
cls
echo 🐳 Video Art Masterpiece - Docker Manager
echo ==========================================
echo.
echo 📊 Current Status:
docker compose ps 2>nul
echo.
echo 🎛️ Management Options:
echo [1] 🚀 Start all services
echo [2] 🛑 Stop all services  
echo [3] 🔄 Restart all services
echo [4] 🔧 Rebuild and restart
echo [5] 📋 View logs
echo [6] 🧹 Clean restart (remove volumes)
echo [7] 💾 Backup data
echo [8] 📊 Resource usage
echo [9] 🌐 Open application
echo [0] ❌ Exit
echo.

set /p choice="Choose option (0-9): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto rebuild
if "%choice%"=="5" goto logs
if "%choice%"=="6" goto clean
if "%choice%"=="7" goto backup
if "%choice%"=="8" goto stats
if "%choice%"=="9" goto open_app
if "%choice%"=="0" goto exit

echo ❌ Invalid option!
timeout /t 2 /nobreak >nul
goto menu

:start
echo.
echo 🚀 Starting Video Art Masterpiece...
docker compose up -d
if errorlevel 1 (
    echo ❌ Failed to start services!
) else (
    echo ✅ Services started successfully!
)
timeout /t 3 /nobreak >nul
goto menu

:stop
echo.
echo 🛑 Stopping all services...
docker compose down
echo ✅ Services stopped!
timeout /t 2 /nobreak >nul
goto menu

:restart
echo.
echo 🔄 Restarting all services...
docker compose restart
echo ✅ Services restarted!
timeout /t 2 /nobreak >nul
goto menu

:rebuild
echo.
echo 🔧 Rebuilding and restarting...
docker compose down
docker compose up --build -d
if errorlevel 1 (
    echo ❌ Failed to rebuild services!
) else (
    echo ✅ Services rebuilt and started!
)
timeout /t 3 /nobreak >nul
goto menu

:logs
echo.
call docker-logs.bat
goto menu

:clean
echo.
echo ⚠️ This will delete all data! Are you sure? (y/N)
set /p confirm="Confirm: "
if /i "%confirm%"=="y" (
    echo 🧹 Clean restart...
    docker compose down -v
    docker compose up --build -d
    echo ✅ Clean restart complete!
) else (
    echo ❌ Cancelled!
)
timeout /t 2 /nobreak >nul
goto menu

:backup
echo.
echo 💾 Creating backup...
set timestamp=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%
set timestamp=%timestamp: =0%
docker run --rm -v video-art-mongodb-data:/data -v %cd%:/backup alpine tar czf /backup/backup_%timestamp%.tar.gz /data
echo ✅ Backup created: backup_%timestamp%.tar.gz
timeout /t 3 /nobreak >nul
goto menu

:stats
echo.
echo 📊 Resource Usage:
docker stats --no-stream
echo.
echo 💾 Disk Usage:
docker system df
echo.
pause
goto menu

:open_app
echo.
echo 🌐 Opening Video Art Masterpiece...
start http://localhost:3000
timeout /t 2 /nobreak >nul
goto menu

:exit
echo.
echo 👋 Thanks for using Video Art Masterpiece!
exit /b 0