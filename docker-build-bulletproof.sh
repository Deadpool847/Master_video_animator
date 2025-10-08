#!/bin/bash

echo "🛠️ Video Art Masterpiece - Bulletproof Docker Build"
echo "=================================================="
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running! Please start Docker first."
    echo "📥 Download from: https://www.docker.com/get-started"
    exit 1
fi

echo "✅ Docker is running"
echo ""

echo "🧹 Cleaning up previous builds..."
docker compose down -v 2>/dev/null
docker system prune -f 2>/dev/null

echo "📦 Creating missing environment files..."
if [ ! -f "backend/.env.docker" ]; then
    cat > backend/.env.docker << EOF
MONGO_URL=mongodb://admin:masterpiece123@mongodb:27017/video_art_masterpiece?authSource=admin
DB_NAME=video_art_masterpiece
CORS_ORIGINS=http://localhost:3000,http://frontend:3000
EOF
    echo "✅ Created backend/.env.docker"
fi

if [ ! -f "frontend/.env.docker" ]; then
    cat > frontend/.env.docker << EOF
REACT_APP_BACKEND_URL=http://localhost:8001
GENERATE_SOURCEMAP=false
EOF
    echo "✅ Created frontend/.env.docker"
fi

echo ""
echo "🔧 Building with multiple retry strategies..."

echo "📦 Step 1: Building Backend (this may take 5-10 minutes)..."
if ! docker build -t video-art-backend -f Dockerfile.backend . --no-cache --progress=plain; then
    echo "⚠️ First backend build attempt failed, trying with different approach..."
    
    # Try with different network setting
    echo "🔄 Trying alternative build strategy..."
    if ! docker build -t video-art-backend -f Dockerfile.backend . --network=host --progress=plain; then
        echo "❌ Backend build failed!"
        echo "🔍 Common solutions:"
        echo "   1. Check your internet connection"
        echo "   2. Restart Docker"
        echo "   3. Clear Docker cache: docker system prune -a"
        echo "   4. Try again in a few minutes"
        exit 1
    fi
fi

echo "✅ Backend build successful!"
echo ""

echo "📦 Step 2: Building Frontend..."
if ! docker build -t video-art-frontend -f Dockerfile.frontend . --no-cache --progress=plain; then
    echo "⚠️ First frontend build attempt failed, trying with different approach..."
    if ! docker build -t video-art-frontend -f Dockerfile.frontend . --network=host --progress=plain; then
        echo "❌ Frontend build failed!"
        echo "🔍 Trying npm cache clean and rebuild..."
        
        # Create a temporary fix Dockerfile
        cat > Dockerfile.frontend.tmp << EOF
FROM node:18-alpine
RUN apk add --no-cache curl bash git
WORKDIR /app
COPY frontend/package.json /app/
RUN npm cache clean --force && npm install --legacy-peer-deps --no-audit
COPY frontend/ /app/
RUN npm run build
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
EOF
        
        if ! docker build -t video-art-frontend -f Dockerfile.frontend.tmp . --progress=plain; then
            echo "❌ All frontend build attempts failed!"
            rm -f Dockerfile.frontend.tmp
            exit 1
        fi
        rm -f Dockerfile.frontend.tmp
    fi
fi

echo "✅ Frontend build successful!"
echo ""

echo "🚀 Step 3: Starting all services..."
if ! docker compose up -d; then
    echo "❌ Failed to start services!"
    echo "🔍 Checking what went wrong..."
    docker compose ps
    docker compose logs --tail=10
    exit 1
fi

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 15

echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "🔍 Quick Health Check:"
if curl -s http://localhost:8001/api/health >/dev/null 2>&1; then
    echo "✅ Backend is responding!"
else
    echo "⚠️ Backend not ready yet (this is normal, may take 1-2 minutes)"
fi

if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ Frontend is responding!"
else
    echo "⚠️ Frontend not ready yet (this is normal, may take 1-2 minutes)"
fi

echo ""
echo "🎉 Build Complete!"
echo ""
echo "🌐 Application URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8001"
echo "  Health Check: http://localhost:8001/api/health"
echo ""
echo "📋 Management Commands:"
echo "  View logs: docker compose logs -f"
echo "  Stop: docker compose down"
echo "  Restart: docker compose restart"
echo ""
echo "🎨 Ready to create video masterpieces!"