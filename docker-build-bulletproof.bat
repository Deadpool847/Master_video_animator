@echo off
echo 🛠️ Video Art Masterpiece - Bulletproof Docker Build
echo ==================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running! Please start Docker Desktop.
    echo 📥 Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo ✅ Docker is running
echo.

echo 🧹 Cleaning up previous builds...
docker compose down -v 2>nul
docker system prune -f 2>nul

echo 📦 Creating missing environment files...
if not exist "backend\.env.docker" (
    echo MONGO_URL=mongodb://admin:masterpiece123@mongodb:27017/video_art_masterpiece?authSource=admin > backend\.env.docker
    echo DB_NAME=video_art_masterpiece >> backend\.env.docker
    echo CORS_ORIGINS=http://localhost:3000,http://frontend:3000 >> backend\.env.docker
    echo ✅ Created backend/.env.docker
)

if not exist "frontend\.env.docker" (
    echo REACT_APP_BACKEND_URL=http://localhost:8001 > frontend\.env.docker
    echo GENERATE_SOURCEMAP=false >> frontend\.env.docker
    echo ✅ Created frontend/.env.docker
)

echo.
echo 🔧 Building with multiple retry strategies...

echo 📦 Step 1: Building Backend (this may take 5-10 minutes)...
docker build -t video-art-backend -f Dockerfile.backend . --no-cache --progress=plain
if errorlevel 1 (
    echo ⚠️ First backend build attempt failed, trying with different approach...
    
    REM Try with different base image
    echo 🔄 Trying alternative build strategy...
    docker build -t video-art-backend -f Dockerfile.backend . --network=host --progress=plain
    
    if errorlevel 1 (
        echo ❌ Backend build failed!
        echo 🔍 Common solutions:
        echo    1. Check your internet connection
        echo    2. Restart Docker Desktop
        echo    3. Clear Docker cache: docker system prune -a
        echo    4. Try again in a few minutes
        pause
        exit /b 1
    )
)

echo ✅ Backend build successful!
echo.

echo 📦 Step 2: Building Frontend...
docker build -t video-art-frontend -f Dockerfile.frontend . --no-cache --progress=plain
if errorlevel 1 (
    echo ⚠️ First frontend build attempt failed, trying with different approach...
    docker build -t video-art-frontend -f Dockerfile.frontend . --network=host --progress=plain
    
    if errorlevel 1 (
        echo ❌ Frontend build failed!
        echo 🔍 Trying npm cache clean and rebuild...
        
        REM Create a temporary fix Dockerfile
        echo FROM node:18-alpine > Dockerfile.frontend.tmp
        echo RUN apk add --no-cache curl bash git >> Dockerfile.frontend.tmp
        echo WORKDIR /app >> Dockerfile.frontend.tmp
        echo COPY frontend/package.json /app/ >> Dockerfile.frontend.tmp
        echo RUN npm cache clean --force ^&^& npm install --legacy-peer-deps --no-audit >> Dockerfile.frontend.tmp
        echo COPY frontend/ /app/ >> Dockerfile.frontend.tmp
        echo RUN npm run build >> Dockerfile.frontend.tmp
        echo FROM nginx:alpine >> Dockerfile.frontend.tmp
        echo COPY --from=0 /app/build /usr/share/nginx/html >> Dockerfile.frontend.tmp
        echo COPY docker/nginx.conf /etc/nginx/conf.d/default.conf >> Dockerfile.frontend.tmp
        echo EXPOSE 3000 >> Dockerfile.frontend.tmp
        echo CMD ["nginx", "-g", "daemon off;"] >> Dockerfile.frontend.tmp
        
        docker build -t video-art-frontend -f Dockerfile.frontend.tmp . --progress=plain
        del Dockerfile.frontend.tmp
        
        if errorlevel 1 (
            echo ❌ All frontend build attempts failed!
            pause
            exit /b 1
        )
    )
)

echo ✅ Frontend build successful!
echo.

echo 🚀 Step 3: Starting all services...
docker compose up -d

if errorlevel 1 (
    echo ❌ Failed to start services!
    echo 🔍 Checking what went wrong...
    docker compose ps
    docker compose logs --tail=10
    pause
    exit /b 1
)

echo.
echo ⏳ Waiting for services to initialize...
timeout /t 15 /nobreak >nul

echo.
echo 📊 Service Status:
docker compose ps

echo.
echo 🔍 Quick Health Check:
curl -s http://localhost:8001/api/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Backend not ready yet (this is normal, may take 1-2 minutes)
) else (
    echo ✅ Backend is responding!
)

curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Frontend not ready yet (this is normal, may take 1-2 minutes)
) else (
    echo ✅ Frontend is responding!
)

echo.
echo 🎉 Build Complete!
echo.
echo 🌐 Application URLs:
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8001
echo   Health Check: http://localhost:8001/api/health
echo.
echo 📋 Management Commands:
echo   View logs: docker compose logs -f
echo   Stop: docker compose down
echo   Restart: docker compose restart
echo.
echo 🎨 Ready to create video masterpieces!

pause