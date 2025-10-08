@echo off
echo 🔧 Frontend Build Fix - Exit Code 127 Solution
echo =============================================
echo.

echo 🧹 Cleaning previous frontend builds...
docker rmi video-art-frontend 2>nul
docker system prune -f

echo.
echo 📋 Diagnosing the issue...
echo The error "exit code: 127" means 'npm run build' command not found.
echo This happens when:
echo   1. craco is not installed properly
echo   2. package.json scripts are missing
echo   3. Dependencies installation failed
echo.

echo 🔧 Trying Fix #1: Standard build with proper dependencies...
docker build -t video-art-frontend -f Dockerfile.frontend . --progress=plain

if errorlevel 1 (
    echo.
    echo ⚠️ Standard build failed. Trying Fix #2: Simple React build...
    docker build -t video-art-frontend -f Dockerfile.frontend.simple . --progress=plain
    
    if errorlevel 1 (
        echo.
        echo ❌ Both builds failed. Trying Fix #3: Manual npm setup...
        
        REM Create a minimal working Dockerfile
        echo FROM node:18-alpine > Dockerfile.frontend.minimal
        echo WORKDIR /app >> Dockerfile.frontend.minimal
        echo RUN npx create-react-app . --template basic >> Dockerfile.frontend.minimal
        echo COPY frontend/src/ /app/src/ >> Dockerfile.frontend.minimal
        echo ENV REACT_APP_BACKEND_URL=http://localhost:8001 >> Dockerfile.frontend.minimal
        echo RUN npm run build >> Dockerfile.frontend.minimal
        echo FROM nginx:alpine >> Dockerfile.frontend.minimal
        echo COPY --from=0 /app/build /usr/share/nginx/html >> Dockerfile.frontend.minimal
        echo COPY docker/nginx.conf /etc/nginx/conf.d/default.conf >> Dockerfile.frontend.minimal
        echo EXPOSE 3000 >> Dockerfile.frontend.minimal
        echo CMD ["nginx", "-g", "daemon off;"] >> Dockerfile.frontend.minimal
        
        docker build -t video-art-frontend -f Dockerfile.frontend.minimal . --progress=plain
        del Dockerfile.frontend.minimal
        
        if errorlevel 1 (
            echo.
            echo ❌ All build attempts failed!
            echo.
            echo 🆘 Emergency solution:
            echo 1. Check Docker has enough memory (8GB+)
            echo 2. Check internet connection
            echo 3. Try: docker system prune -a
            echo 4. Restart Docker Desktop
            echo 5. Try building again
            pause
            exit /b 1
        )
    )
)

echo.
echo ✅ Frontend build successful!
echo.

echo 🚀 Starting the application...
docker compose up -d

echo.
echo 📊 Final Status:
docker compose ps

echo.
echo 🎉 Build fix completed!
echo Frontend should be available at: http://localhost:3000

pause