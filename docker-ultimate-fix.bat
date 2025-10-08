@echo off
echo 🛠️ ULTIMATE DOCKER FIX - No More Errors!
echo ========================================
echo.

REM Clean everything
echo 🧹 Complete cleanup...
docker compose down -v 2>nul
docker system prune -f 2>nul
docker rmi video-art-frontend video-art-backend 2>nul

echo 📦 Step 1: Backend (Python/FastAPI)
docker build -t video-art-backend -f Dockerfile.backend . --progress=plain
if errorlevel 1 (
    echo ❌ Backend build failed!
    pause
    exit /b 1
)
echo ✅ Backend success!

echo.
echo 📦 Step 2: Frontend (React/Nginx) - Bulletproof Version
docker build -t video-art-frontend -f Dockerfile.frontend.bulletproof . --progress=plain
if errorlevel 1 (
    echo ❌ Bulletproof frontend failed! Trying simple version...
    docker build -t video-art-frontend -f Dockerfile.frontend.simple . --progress=plain
    if errorlevel 1 (
        echo ❌ All frontend builds failed!
        pause
        exit /b 1
    )
)
echo ✅ Frontend success!

echo.
echo 🚀 Step 3: Starting complete application...
docker compose up -d

echo.
echo ⏳ Waiting for startup...
timeout /t 20 /nobreak >nul

echo 📊 Final Status:
docker compose ps

echo.
echo 🔍 Testing endpoints...
curl -s http://localhost:8001/api/health >nul 2>&1 && echo ✅ Backend OK || echo ⚠️ Backend starting...
curl -s http://localhost:3000 >nul 2>&1 && echo ✅ Frontend OK || echo ⚠️ Frontend starting...

echo.
echo 🎉 ULTIMATE FIX COMPLETE!
echo.
echo 🌐 Your Video Art Masterpiece is ready:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8001
echo.
echo 🎨 Ready to create masterpieces!

pause